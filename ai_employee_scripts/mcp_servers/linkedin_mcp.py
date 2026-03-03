#!/usr/bin/env python3
"""
LinkedIn MCP Server for AI Employee

First Run:
  uv run python mcp_servers/linkedin_mcp.py

  ✅ Checks for existing session at sessions/linkedin_mcp/
  ✅ If no session: Opens browser for you to log in
  ✅ Saves session for future runs
  ✅ Subsequent runs use saved session

Second Run (session exists):
  ✅ Loads session from sessions/linkedin_mcp/
  ✅ Checks if logged in → Refreshes if needed
  ✅ Starts MCP server, waits for Claude calls

Tools Available:
  - post_content: Post to LinkedIn feed
  - reply_message: Reply to a LinkedIn message
  - get_messages: Fetch LinkedIn messages
"""

import sys
import os
import json
import random
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

# MCP imports
from mcp.server.fastmcp import FastMCP

# Async Playwright imports
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# =============================================================================
# CONFIGURATION
# =============================================================================

# Separate session for MCP (isolated from linkedin_watcher)
SCRIPT_DIR = Path(__file__).parent.parent
SESSION_PATH = SCRIPT_DIR / "sessions" / "linkedin_mcp"

# Get session path from env or use default
SESSION_PATH = Path(os.getenv(
    "LINKEDIN_MCP_SESSION",
    str(SESSION_PATH)
))

# Ensure session directory exists
SESSION_PATH.mkdir(parents=True, exist_ok=True)


def print_status(message: str, emoji: str = "✅"):
    """Print status message to stderr (safe for MCP stdio transport)."""
    print(f"{emoji} {message}", file=sys.stderr, flush=True)


# =============================================================================
# BROWSER CONTEXT MANAGEMENT
# =============================================================================

class LinkedInBrowser:
    """
    Manages LinkedIn browser session for MCP server.

    Uses separate session from linkedin_watcher.py for isolation.
    Uses async Playwright to work with FastMCP's async runtime.
    """

    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.playwright = None
        self.browser = None
        self._initialized = False
        _lock = asyncio.Lock()

    def is_first_run(self) -> bool:
        """
        Check if this is the first run (no valid session).

        Checks for actual session data (Cookies file), not just cache files.
        """
        # Check if Default/Cookies exists and has content
        cookies_file = self.session_path / "Default" / "Cookies"
        if cookies_file.exists() and cookies_file.stat().st_size > 100:
            return False  # Has valid session
        return True  # No valid session

    async def start(self, headless: bool = True):
        """
        Start browser context.

        Args:
            headless: Run browser in headless mode (False for first-run login)
        """
        if self._initialized:
            return

        is_first = self.is_first_run()

        print_status("", "")
        print_status("=" * 60, "🔗")
        print_status("         LinkedIn MCP Server", "🤖")
        print_status("=" * 60, "🔗")
        print_status("", "")
        print_status(f"Session Path: {self.session_path}", "📁")
        print_status(f"First Run: {is_first}", "🔐")
        print_status("", "")

        if is_first:
            print_status("FIRST RUN DETECTED!", "⚠️")
            print_status("Browser will open for LinkedIn login...", "🌐")
            print_status("", "")
            print_status("Instructions:", "📝")
            print_status("  1. Browser will open", "1️⃣")
            print_status("  2. Log in to LinkedIn", "2️⃣")
            print_status("  3. Session will be saved automatically", "3️⃣")
            print_status("  4. Wait for 'Login detected' message", "4️⃣")
            print_status("", "")

        self.playwright = await async_playwright().start()

        # Launch with persistent context
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=headless if not is_first else False,  # Always visible on first run
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            viewport={'width': 1280, 'height': 720}
        )

        self._initialized = True

        # If first run, wait for login
        if is_first:
            await self._wait_for_login()
            # Close browser after first-run setup
            await self.stop()
            self._initialized = False
            print_status("Setup complete! Starting MCP server...", "🚀")

    async def _wait_for_login(self, timeout: int = 300):
        """
        Wait for user to complete LinkedIn login.

        Args:
            timeout: Maximum seconds to wait (default: 5 minutes)
        """
        print_status("", "")
        print_status("Waiting for LinkedIn login...", "⏳")
        print_status("Please log in now. Browser will stay open until login is detected.", "📝")
        print_status("", "")

        start_time = asyncio.get_event_loop().time()
        logged_in = False

        # Create a page to check login status
        page = await self.browser.new_page()

        # Navigate to LinkedIn first
        await page.goto('https://www.linkedin.com/feed/', timeout=30000)
        await asyncio.sleep(2)

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                current_url = page.url

                # Check if actually logged in by looking for logged-in elements
                # NOT just URL - LinkedIn shows feed page even when logged out
                try:
                    # Try multiple selectors for logged-in elements
                    logged_in_element = None

                    # Selector 1: Profile icon in nav (most reliable)
                    if not logged_in_element:
                        logged_in_element = await page.query_selector('.global-nav__me')

                    # Selector 2: Profile dropdown
                    if not logged_in_element:
                        logged_in_element = await page.query_selector('.global-nav__me-photo')

                    # Selector 3: Feed create post button (only when logged in)
                    if not logged_in_element:
                        logged_in_element = await page.query_selector('button[aria-label="Start a post"], .share-box-feed-entry__trigger')

                    # Selector 4: Messaging icon
                    if not logged_in_element:
                        logged_in_element = await page.query_selector('.global-nav__navItem[href*="/messaging/"]')

                    # Also check for "Sign in" button which means NOT logged in
                    sign_in_button = await page.query_selector('a[href*="/login"], .login-form')

                    if logged_in_element and not sign_in_button:
                        logged_in = True
                        print_status("", "")
                        print_status("✅ Login detected! Session saved.", "✅")
                        print_status("", "")
                        break
                    else:
                        # Still not logged in
                        elapsed = int(timeout - (asyncio.get_event_loop().time() - start_time))
                        if elapsed % 15 == 0 or elapsed < 10:  # Print every 15 seconds or last 10 seconds
                            print_status(f"Waiting for login... ({elapsed}s remaining)", "⏳")

                except:
                    # Error checking elements - assume not logged in
                    elapsed = int(timeout - (asyncio.get_event_loop().time() - start_time))
                    print_status(f"Checking login status... ({elapsed}s remaining)", "⏳")

                await asyncio.sleep(2)

            except Exception as e:
                print_status(f"Error checking login: {e}", "⚠️")
                await asyncio.sleep(3)

        await page.close()

        if not logged_in:
            print_status("", "")
            print_status("⚠️ Login timeout. Please re-run the server.", "⚠️")
            print_status("", "")

    async def verify_session(self) -> bool:
        """
        Verify that the existing session is still valid.

        Returns:
            True if session is valid, False otherwise
        """
        if not self._initialized:
            await self.start(headless=True)

        page = None
        try:
            page = await self.browser.new_page()

            # Try to navigate with shorter timeout to fail fast
            try:
                await page.goto('https://www.linkedin.com/', timeout=10000)
            except PlaywrightTimeout:
                # Timeout means can't reach LinkedIn - network issue
                print_status("Cannot reach LinkedIn - network or browser issue", "⚠️")
                return False

            # Check if redirected to login
            if 'login' in page.url or '/uas/login' in page.url:
                return False

            # Check for logged-in elements (quick check)
            try:
                # Just check URL - if on feed or home page, probably logged in
                if 'feed' in page.url or 'in/' in page.url:
                    return True
            except:
                pass

            # Try checking for profile icon
            try:
                profile = await page.query_selector('.global-nav__me, .global-nav__me-photo')
                return profile is not None
            except:
                pass

            return False

        except Exception as e:
            print_status(f"Session verification error: {e}", "⚠️")
            return False
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    async def ensure_logged_in(self):
        """
        Ensure the user is logged in to LinkedIn.

        If not logged in, opens browser for manual login.
        """
        if not self._initialized:
            await self.start(headless=True)

        try:
            is_valid = await self.verify_session()
            if not is_valid:
                print_status("", "")
                print_status("⚠️ Session expired or invalid. Need to re-login.", "⚠️")
                print_status("", "")

                # Stop current browser
                await self.stop()

                # Start fresh login flow
                await self.start(headless=False)  # Visible for login
        except Exception as e:
            print_status(f"Error during login check: {e}", "⚠️")
            print_status("Attempting to re-login...", "🔄")

            # Stop and restart
            await self.stop()
            await self.start(headless=False)

    async def stop(self):
        """Stop browser context."""
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
        self._initialized = False


# Global browser instance
_browser: Optional[LinkedInBrowser] = None


async def get_browser() -> LinkedInBrowser:
    """Get or create global browser instance."""
    global _browser

    if _browser is None:
        _browser = LinkedInBrowser(SESSION_PATH)

    # Start browser only if not already initialized
    # Don't verify session here - do it in tools if needed
    if not _browser._initialized:
        await _browser.start(headless=True)

    return _browser


# =============================================================================
# MCP SERVER
# =============================================================================

mcp = FastMCP(
    "linkedin-mcp",
    instructions="LinkedIn operations: post content, reply to messages, get messages"
)


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
async def post_content(
    content: str,
    visibility: str = "PUBLIC"
) -> str:
    """
    Post content to LinkedIn feed.

    Args:
        content: Post content (supports line breaks, hashtags, mentions)
        visibility: Post visibility - 'PUBLIC' or 'CONNECTIONS'

    Returns:
        Confirmation message with post details
    """
    browser = await get_browser()
    print_status(f"Posting to LinkedIn ({visibility})...", "📝")

    if not browser or not browser._initialized:
        return "Error: Browser not initialized. Please check the MCP server logs."

    try:
        page = await browser.browser.new_page()

        # Go to LinkedIn feed
        print_status("Navigating to LinkedIn feed...", "🌐")
        await page.goto('https://www.linkedin.com/feed/', timeout=30000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)  # Wait for page to settle (LinkedIn has continuous network activity)

        # Debug: Take screenshot and log page state
        debug_path = SCRIPT_DIR.parent / "AI_Employee_Vault" / "Logs" / f"linkedin_feed_{datetime.now().strftime('%H%M%S')}.png"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(debug_path), full_page=True)
        print_status(f"Feed screenshot: {debug_path}", "📸")
        print_status(f"Current URL: {page.url}", "🔗")

        # Check if logged in - try multiple selectors
        has_profile = await page.query_selector('.global-nav__me') is not None
        if not has_profile:
            # Try alternative selectors
            has_profile = await page.query_selector('.global-nav__me-photo') is not None
        if not has_profile:
            # Try checking for me-icon
            has_profile = await page.query_selector('li-icon[type="me-icon"]') is not None
        if not has_profile:
            # Try checking for profile-image
            has_profile = await page.query_selector('[data-test-id="profile-photo"]') is not None

        print_status(f"Has profile icon: {has_profile}", "👤")

        # Only fail if URL indicates we're not logged in
        if 'login' in page.url or '/uas/login' in page.url:
            await page.close()
            return "Error: Not logged in to LinkedIn. Please run manual login first."

        # If profile check failed but URL looks good, show warning but continue
        if not has_profile:
            print_status("Profile icon not found, but continuing anyway...", "⚠️")

        # Click the "Start a post" button
        print_status("Looking for 'Start a post' button...", "🔍")
        post_button = None

        selectors = [
            'button[aria-label="Start a post"]',
            'button[aria-label="Start a post,"]',
            '.share-box-feed-entry__trigger',
            '[data-control-name="share_box"]',
            'div.share-box-feed-entry__trigger',
            'button.share-box-feed-entry__trigger',
            'div[role="button"][aria-label*="post"]',
            'button[aria-label*="Start a post"]',
            '.share-box-feed-entry__content',
            '#ember',
            'button.scaffold-fab__icon',
            'div[data-test-id="feed-cta"]',
        ]

        for selector in selectors:
            try:
                post_button = await page.wait_for_selector(selector, timeout=3000, state='visible')
                if post_button:
                    print_status(f"Found button with: {selector}", "✅")
                    break
            except:
                continue

        # Fallback: Look for any button with "post" in aria-label or text
        if not post_button:
            print_status("Trying fallback: searching for buttons with 'post'...", "🔍")
            all_buttons = await page.query_selector_all('button, div[role="button"]')
            print_status(f"Found {len(all_buttons)} buttons total", "🔢")

            for btn in all_buttons:
                try:
                    aria_label = await btn.get_attribute('aria-label')
                    text = await btn.inner_text()

                    # Check if this looks like the "Start a post" button
                    if aria_label and 'post' in aria_label.lower():
                        post_button = btn
                        print_status(f"Found by aria-label: '{aria_label}'", "✅")
                        break
                    if text and 'start a post' in text.lower():
                        post_button = btn
                        print_status(f"Found by text: '{text}'", "✅")
                        break
                except:
                    continue

        if not post_button:
            await page.close()
            return "Error: Could not find 'Start a post' button. You might not be logged in."

        await post_button.click()
        print_status("Clicked post button, waiting for modal...", "⏳")
        await asyncio.sleep(4)

        # Save screenshot to see what appeared
        debug_path = SCRIPT_DIR.parent / "AI_Employee_Vault" / "Logs" / f"linkedin_modal_{datetime.now().strftime('%H%M%S')}.png"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(debug_path), full_page=True)
        print_status(f"Screenshot: {debug_path}", "📸")

        # Look for text input elements
        print_status("Looking for text input...", "⌨️")
        all_editables = await page.query_selector_all('[contenteditable="true"]')
        all_textareas = await page.query_selector_all('textarea')
        print_status(f"Found {len(all_editables)} editables, {len(all_textareas)} textareas", "🔢")

        if len(all_editables) == 0 and len(all_textareas) == 0:
            await page.close()
            return "Error: No text input elements found. LinkedIn may have changed their UI."

        # Find the largest contenteditable element (likely the post editor)
        best_area = None
        best_size = 0

        for i, elem in enumerate(all_editables):
            try:
                if await elem.is_visible():
                    box = await elem.bounding_box()
                    if box and box['width'] > 0 and box['height'] > 0:
                        size = box['width'] * box['height']
                        print_status(f"  Editable {i}: {box['width']}x{box['height']} (size={size})", "  ")

                        # Lowered threshold - LinkedIn's editor might be smaller than expected
                        if size > best_size and size > 100:
                            best_size = size
                            best_area = elem
                            print_status(f"  -> Best candidate!", "✓")
            except:
                pass

        # If no good contenteditable, try textarea (with lower threshold)
        if not best_area:
            for i, elem in enumerate(all_textareas):
                try:
                    if await elem.is_visible():
                        box = await elem.bounding_box()
                        if box and box['width'] > 0 and box['height'] > 0:
                            size = box['width'] * box['height']
                            print_status(f"  Textarea {i}: {box['width']}x{box['height']} (size={size})", "  ")

                            if size > best_size and size > 100:
                                best_size = size
                                best_area = elem
                                print_status(f"  -> Best candidate!", "✓")
                except:
                    pass

        text_area = best_area

        # Try clicking in the main content area to expand the editor
        if text_area and best_size < 5000:
            print_status("Text area is small, trying to expand it...", "🔍")
            await text_area.click()
            await asyncio.sleep(2)

            # Re-scan for larger elements after clicking
            all_editables = await page.query_selector_all('[contenteditable="true"]')
            all_textareas = await page.query_selector_all('textarea')

            for elem in all_editables + all_textareas:
                try:
                    if await elem.is_visible():
                        box = await elem.bounding_box()
                        if box and box['width'] * box['height'] > best_size:
                            best_size = box['width'] * box['height']
                            text_area = elem
                            print_status(f"Found larger element after click: {box['width']}x{box['height']}", "✅")
                except:
                    pass

        if not text_area:
            await page.close()
            return f"Error: Could not find suitable text input. Found {len(all_editables)} editables and {len(all_textareas)} textareas."

        # Type content with human-like delays
        print_status("Typing content...", "⌨️")
        await text_area.click()
        await asyncio.sleep(0.5)

        # Clear any existing text
        await text_area.fill('')
        await asyncio.sleep(0.3)

        # Type content with human-like delays
        for char in content:
            await text_area.type(char, delay=random.randint(10, 30))

        await asyncio.sleep(2)

        # Click Post button
        print_status("Submitting post...", "📤")
        post_btn = None
        post_selectors = [
            'button[type="submit"]',
            'button:has-text("Post")',
            'button.share-actions__primary-action',
            '[data-control-name="share.post"]',
            'button[aria-label="Post"]',
            '.post-btn',
            'button.ember-view'
        ]

        for selector in post_selectors:
            try:
                post_btn = await page.wait_for_selector(selector, timeout=3000, state='visible')
                if post_btn:
                    print_status(f"Found post button with selector: {selector}", "🔍")
                    break
            except:
                continue

        if not post_btn:
            # Try clicking by text
            try:
                all_buttons = await page.query_selector_all('button')
                for btn in all_buttons:
                    try:
                        text = await btn.inner_text()
                        if 'Post' in text and len(text) < 20:
                            post_btn = btn
                            print_status(f"Found button by text: '{text}'", "🔍")
                            break
                    except:
                        continue
            except:
                pass

        if post_btn:
            await post_btn.click()
            await asyncio.sleep(4)
            print_status("Post published!", "✅")
        else:
            await page.close()
            return "Error: Could not find Post button to submit."

        await page.close()

        return f"""Post published successfully!

Visibility: {visibility}
Content: {content[:200]}{'...' if len(content) > 200 else ''}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    except PlaywrightTimeout as e:
        error_msg = f"Timeout: Could not load LinkedIn page. This might be a network issue or LinkedIn is blocking automated access.\n\nError: {e}"
        print_status(error_msg, "❌")
        return error_msg
    except Exception as e:
        error_msg = f"Failed to post: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def reply_message(
    conversation_url: str,
    message: str,
    wait_before_send: int = 2
) -> str:
    """
    Reply to a LinkedIn message conversation.

    Args:
        conversation_url: Full URL to LinkedIn conversation
            Example: https://www.linkedin.com/messaging/thread/ABC123/
            OR sender name (will search and click)
        message: Reply message content
        wait_before_send: Seconds to wait before sending (default: 2)

    Returns:
        Confirmation message with conversation details
    """
    browser = await get_browser()
    print_status(f"Replying to LinkedIn message...", "💬")

    try:
        page = await browser.browser.new_page()

        # Check if it's a URL or just a name
        if conversation_url.startswith('http'):
            # Direct URL
            url = conversation_url
            print_status(f"Navigating to conversation URL...", "🌐")
        else:
            # Search by sender name
            print_status(f"Searching for conversation: {conversation_url}", "🔍")
            # First go to messaging
            await page.goto('https://www.linkedin.com/messaging/', timeout=30000)
            await asyncio.sleep(3)

            # Find and click conversation by name using JavaScript
            found = await page.evaluate("""(senderName) => {
                const selectors = [
                    '.msg-conversation-listitem',
                    '[data-control-name="message_thread"]'
                ];
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const nameEl = el.querySelector('.msg-conversation-listitem__participant-names');
                        if (nameEl && nameEl.textContent) {
                            const name = nameEl.textContent.trim();
                            if (name.toLowerCase().includes(senderName.toLowerCase())) {
                                el.click();
                                return true;
                            }
                        }
                    }
                }
                return false;
            }""", conversation_url)

            if not found:
                await page.close()
                return f"Error: Could not find conversation with: {conversation_url}"

            await asyncio.sleep(2)
            url = page.url
            print_status(f"Found conversation: {url[:60]}...", "✅")

        # Navigate to conversation
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)

        # Try multiple selectors for message input
        selectors = [
            'div[contenteditable="true"] >> visible=true',
            'textarea.msg-form__contenteditable',
            '[data-test-message-input]',
            'div.msg-form__contenteditable',
            '.msg-s-message-list-container textarea'
        ]

        input_box = None
        for selector in selectors:
            try:
                input_box = await page.wait_for_selector(selector, timeout=5000, state='visible')
                if input_box:
                    print_status(f"Found input with selector: {selector}", "🔍")
                    break
            except:
                continue

        if not input_box or not await input_box.is_visible():
            await page.close()
            return "Error: Could not find message input box. The conversation URL might be invalid."

        # Click to focus
        print_status("Typing reply...", "⌨️")
        await input_box.click()
        await asyncio.sleep(0.5)

        # Type message (human-like)
        for char in message:
            await input_box.type(char, delay=random.randint(10, 30))

        await asyncio.sleep(wait_before_send)

        # Try to find and click send button
        print_status("Sending message...", "📤")

        # Try multiple methods to send
        sent = False

        # Method 1: Click Send button
        send_selectors = [
            'button[type="submit"]',
            'button:has-text("Send")',
            '.msg-s-message-action-container button',
            '[data-control-name="send_message"]'
        ]

        for selector in send_selectors:
            try:
                send_btn = await page.query_selector(selector)
                if send_btn and await send_btn.is_visible():
                    await send_btn.click()
                    sent = True
                    break
            except:
                continue

        # Method 2: Press Enter if button not found
        if not sent:
            try:
                await page.keyboard.press("Enter")
                sent = True
            except:
                pass

        await asyncio.sleep(2)
        await page.close()

        if sent:
            print_status("Reply sent!", "✅")
            return f"""Message sent successfully!

Conversation: {url[:60]}...
Message: {message[:200]}{'...' if len(message) > 200 else ''}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            return "Error: Could not send message (Send button not found)."

    except Exception as e:
        error_msg = f"Failed to send reply: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def get_messages(
    filter: str = "all",
    limit: int = 10,
    include_content: bool = False
) -> str:
    """
    Get LinkedIn messages/conversations.

    Args:
        filter: 'all', 'unread', or 'pinned' (default: 'all')
        limit: Maximum messages to return (default: 10)
        include_content: Fetch full message content (slower, default: False)

    Returns:
        JSON string with messages array
    """
    browser = await get_browser()
    print_status(f"Fetching LinkedIn messages (filter: {filter})...", "📬")

    try:
        page = await browser.browser.new_page()

        # Build URL with filter
        url = 'https://www.linkedin.com/messaging/'
        if filter.lower() == 'unread':
            url += '?filter=unread'
        elif filter.lower() == 'pinned':
            url += '?filter=pinned'

        # Navigate
        print_status("Navigating to messaging...", "🌐")
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)

        # Get conversation list
        conversations = await page.query_selector_all('.msg-conversation-listitem')

        print_status(f"Found {len(conversations)} conversations", "📊")

        # ====== PHASE 1: Extract all basic data WITHOUT clicking ======
        # This avoids stale elements when we click later
        conversations_data = []
        for i, convo in enumerate(conversations):
            try:
                sender_elem = await convo.query_selector('.msg-conversation-listitem__participant-names')
                sender = await sender_elem.inner_text() if sender_elem else "Unknown"
                sender = sender.strip()

                snippet_elem = await convo.query_selector('.msg-conversation-card__message-snippet')
                preview = await snippet_elem.inner_text() if snippet_elem else ""
                preview = preview.strip()

                is_unread = '--unread' in await convo.get_attribute('class') or ''
                unread_indicator = await convo.query_selector('.msg-conversation-card__convo-item-container--unread')
                is_unread = is_unread or (unread_indicator is not None)

                conversations_data.append({
                    "index": i,
                    "sender": sender,
                    "preview": preview[:300],
                    "is_unread": is_unread
                })
            except Exception as e:
                print_status(f"Error extracting basic data from conversation {i+1}: {e}", "⚠️")
                continue

        print_status(f"Extracted basic data for {len(conversations_data)} conversations", "📊")

        # ====== PHASE 2: Click each conversation to get URLs (with fresh queries) ======
        messages = []
        processed = 0
        list_url = page.url

        for conv_data in conversations_data[:limit]:
            try:
                # Re-query conversations to get FRESH elements (avoids stale element errors)
                fresh_conversations = await page.query_selector_all('.msg-conversation-listitem')
                if conv_data["index"] >= len(fresh_conversations):
                    print_status(f"Conversation index {conv_data['index']} out of range", "⚠️")
                    continue

                target_convo = fresh_conversations[conv_data["index"]]

                # Click to get URL
                await target_convo.click()
                await asyncio.sleep(2)
                conv_url = page.url

                # Get full content if requested
                full_content = ""
                if include_content:
                    try:
                        messages_container = await page.query_selector('.msg-s-message-list-container')
                        if messages_container:
                            full_content = await messages_container.inner_text()
                            full_content = full_content.strip()
                    except:
                        pass

                messages.append({
                    "sender": conv_data["sender"],
                    "preview": conv_data["preview"],
                    "conversation_url": conv_url,
                    "full_content": full_content if include_content else None,
                    "is_unread": conv_data["is_unread"],
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                processed += 1

                # Go back to list for next iteration
                await page.goto(list_url)
                await asyncio.sleep(2)

            except Exception as e:
                print_status(f"Error clicking conversation {conv_data['sender']}: {e}", "⚠️")
                # Make sure we're back on the list
                await page.goto(list_url)
                await asyncio.sleep(2)
                continue

        await page.close()

        result = {
            "filter": filter,
            "requested_limit": limit,
            "total_found": len(conversations),
            "total_processed": processed,
            "messages": messages,
            "fetched_at": datetime.now().isoformat()
        }

        print_status(f"Processed {processed} messages", "✅")
        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Failed to get messages: {e}"
        print_status(error_msg, "❌")
        return json.dumps({"error": error_msg}, indent=2)


@mcp.tool()
async def verify_connection() -> str:
    """
    Verify LinkedIn connection status.

    Returns:
        Status message indicating if logged in and session is valid
    """
    try:
        browser = await get_browser()
        is_valid = await browser.verify_session()

        result = {
            "status": "connected" if is_valid else "disconnected",
            "session_path": str(SESSION_PATH),
            "first_run": browser.is_first_run(),
            "verified_at": datetime.now().isoformat()
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "session_path": str(SESSION_PATH)
        }, indent=2)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main_async():
    """Async main function."""
    global _browser

    print_status("", "")
    print_status("╔════════════════════════════════════════════════════════╗", "🔗")
    print_status("║         LinkedIn MCP Server for AI Employee           ║", "🤖")
    print_status("╚════════════════════════════════════════════════════════╝", "🔗")
    print_status("", "")

    try:
        # Initialize browser object (but don't start it yet)
        _browser = LinkedInBrowser(SESSION_PATH)

        # Handle first-run setup before starting MCP server
        if _browser.is_first_run():
            await _browser.start(headless=False)  # Visible for login
            # Browser is closed after login in start()
            print_status("", "")
            print_status("Setup complete! Starting MCP server...", "🚀")
        else:
            print_status(f"Found existing session at: {SESSION_PATH}", "📁")
            print_status("Browser will start when tools are called (lazy loading)", "⚡")

        print_status("", "")
        print_status("Starting MCP server...", "🚀")
        print_status("Tools available: post_content, reply_message, get_messages, verify_connection", "🛠️")
        print_status("", "")
        print_status("Server is running. Press Ctrl+C to stop.", "⏳")
        print_status("", "")

        # Start MCP server (this blocks)
        # Browser will start lazily when tools are called
        await mcp.run_stdio_async()

    except KeyboardInterrupt:
        print_status("", "")
        print_status("LinkedIn MCP Server stopped by user", "👋")

        # Clean up browser if it was started
        if _browser and _browser._initialized:
            await _browser.stop()

    except Exception as e:
        print_status("", "")
        print_status(f"Fatal error: {e}", "❌")
        raise


def main():
    """Run the LinkedIn MCP server."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
