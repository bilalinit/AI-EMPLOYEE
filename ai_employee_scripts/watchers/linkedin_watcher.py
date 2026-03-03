"""
LinkedIn Watcher - Monitors LinkedIn for messages and engagement

Monitors LinkedIn for new messages, connection requests, and post engagement
using Playwright browser automation.

Usage:
    python linkedin_watcher.py
"""

import logging
import time
from pathlib import Path
from typing import List
from datetime import datetime
import sys

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Add parent directory to import error_recovery
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_watcher import BaseWatcher
from error_recovery import with_retry, is_transient_error


class LinkedInWatcher(BaseWatcher):
    """
    LinkedIn Watcher - monitors LinkedIn for important activity.

    Uses Playwright to automate LinkedIn Web (no official API needed).
    Requires LinkedIn login on first run.
    """

    def __init__(
        self,
        vault_path: str,
        session_path: str = None,
        check_interval: int = 300
    ):
        """
        Initialize the LinkedIn watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            session_path: Path to store LinkedIn session (for persisting login)
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        super().__init__(vault_path, check_interval, name="LinkedInWatcher")

        # Set up session path
        scripts_dir = Path(__file__).parent.parent
        if session_path:
            self.session_path = Path(session_path)
        else:
            self.session_path = scripts_dir / "sessions" / "linkedin"
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Add Inbox path for storing full LinkedIn messages
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)

        # Check if this is first run (no session file exists)
        self.first_run = not any(self.session_path.iterdir())
        """
        Initialize the LinkedIn watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            session_path: Path to store LinkedIn session (for persisting login)
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        super().__init__(vault_path, check_interval, name="LinkedInWatcher")

        # Set up session path
        scripts_dir = Path(__file__).parent.parent
        if session_path:
            self.session_path = Path(session_path)
        else:
            self.session_path = scripts_dir / "sessions" / "linkedin"
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Track seen items
        self.seen_messages = set()
        self.seen_requests = set()
        self._load_state()

    def _load_state(self):
        """Load previously seen item IDs."""
        state_file = self.vault_path / "Logs" / "linkedin_state.json"
        if state_file.exists():
            import json
            try:
                state = json.loads(state_file.read_text())
                self.seen_messages = set(state.get('messages', []))
                self.seen_requests = set(state.get('requests', []))
            except:
                pass

    def _save_state(self):
        """Save seen item IDs to state file."""
        state_file = self.vault_path / "Logs"
        state_file.mkdir(parents=True, exist_ok=True)
        state_file = state_file / "linkedin_state.json"
        import json
        state = {
            'messages': list(self.seen_messages),
            'requests': list(self.seen_requests)
        }
        state_file.write_text(json.dumps(state, indent=2))

    def _create_browser_context(self, headless: bool = True):
        """Create a persistent browser context for LinkedIn."""
        p = sync_playwright().start()
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        return p, browser

    def check_for_updates(self) -> List:
        """Check for new LinkedIn activity."""
        updates = []

        self.logger.info("Starting LinkedIn check...")

        try:
            # Use visible browser on first run for authentication
            use_headless = not self.first_run
            self.logger.info(f"Creating browser context (headless={use_headless})...")
            p, browser = self._create_browser_context(headless=use_headless)
            self.logger.info("Browser context created successfully")

            try:
                self.logger.info("Creating new page...")
                page = browser.new_page()
                self.logger.info("Navigating to LinkedIn messaging...")
                # Use URL that goes directly to unread filter without auto-opening messages
                page.goto('https://www.linkedin.com/messaging/?filter=unread', timeout=30000)
                self.logger.info("Waiting for network idle...")

                # On first run, wait for user to complete login
                if self.first_run:
                    self.logger.info("=" * 50)
                    self.logger.info("FIRST RUN: Please log in to LinkedIn")
                    self.logger.info("Waiting for authentication to complete...")
                    self.logger.info("=" * 50)

                    # Wait for successful login - check for messaging elements that only appear when logged in
                    max_wait = 120  # 2 minutes max wait time
                    start_time = time.time()
                    logged_in = False

                    while time.time() - start_time < max_wait:
                        try:
                            # Check if we're on messaging page (means logged in)
                            # or if we're on login page
                            current_url = page.url
                            self.logger.info(f"Current URL: {current_url}")

                            if 'login' in current_url:
                                self.logger.info("Still on login page, waiting...")
                            elif 'checkpoint' in current_url or 'challenge' in current_url:
                                self.logger.info("Security verification detected, waiting...")
                            elif 'messaging' in current_url:
                                # We're on messaging page - logged in!
                                logged_in = True
                                self.logger.info("✅ Detected logged in state!")
                                break
                            time.sleep(3)
                        except Exception as e:
                            self.logger.warning(f"Login check error: {e}")
                            time.sleep(3)

                    if not logged_in:
                        self.logger.warning("Login timeout - will try again on next run")
                        return updates

                page.wait_for_load_state('domcontentloaded', timeout=30000)
                self.logger.info("Page loaded successfully")

                # Wait a bit for messages to render
                import time
                time.sleep(2)
                self.logger.info("Waited for initial page load")

                # Close the conversation detail panel if it's open (prevents auto-opening first message)
                try:
                    close_button = page.query_selector('.msg-thread__close-icon, .artdeco-button[data-test-conversation-close-icon="true"]')
                    if close_button:
                        close_button.click()
                        self.logger.info("Closed conversation detail panel")
                        time.sleep(1)
                except:
                    self.logger.info("No conversation panel to close (or already closed)")

                # Wait a bit more for messages to stabilize
                time.sleep(2)
                self.logger.info("Waited for messages to render")

                # Wait for conversation list to load
                try:
                    page.wait_for_selector('.msg-conversation-listitem', timeout=10000)
                    self.logger.info("Conversation list loaded")
                except:
                    self.logger.warning("Timeout waiting for conversation list")

                # Debug: Save screenshot and HTML to see what's on the page
                screenshot_path = self.vault_path / "Logs" / "linkedin_debug.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                self.logger.info(f"Screenshot saved to {screenshot_path}")

                html_path = self.vault_path / "Logs" / "linkedin_debug.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(page.content())
                self.logger.info(f"HTML dump saved to {html_path}")

                # Debug: Check what's on the page
                all_conversations = page.query_selector_all('.msg-conversation-listitem')
                self.logger.info(f"Total conversations on page: {len(all_conversations)}")

                # Check for unread messages - iterate all conversations and check for unread indicators
                self.logger.info("Checking for unread messages...")
                unread_count = 0
                for i, convo in enumerate(all_conversations):
                    try:
                        # Debug: log all classes of this conversation
                        convo_class = convo.get_attribute('class') or ''
                        self.logger.info(f"  Conversation {i+1} classes: {convo_class[:200]}")

                        # Check if this conversation is unread (look for --unread class in any child)
                        unread_indicator = convo.query_selector('.msg-conversation-card__convo-item-container--unread')
                        if not unread_indicator:
                            # Try alternative check - unread snippet class
                            unread_indicator = convo.query_selector('.msg-conversation-card__message-snippet--unread')

                        if unread_indicator:
                            unread_count += 1
                            # Extract sender name
                            sender_elem = convo.query_selector('.msg-conversation-listitem__participant-names')
                            sender_name = sender_elem.inner_text().strip() if sender_elem else "Unknown"

                            # Extract message preview
                            snippet_elem = convo.query_selector('.msg-conversation-card__message-snippet')
                            preview = snippet_elem.inner_text().strip() if snippet_elem else ""

                            # Create unique ID from sender + preview
                            msg_id = str(hash(f"{sender_name}:{preview}"))

                            if msg_id not in self.seen_messages:
                                updates.append({
                                    'type': 'message',
                                    'id': msg_id,
                                    'sender': sender_name,
                                    'preview': preview[:200]
                                })
                                self.seen_messages.add(msg_id)
                                self.logger.info(f"  New unread from {sender_name}: {preview[:50]}...")
                            else:
                                self.logger.info(f"  Already seen unread from {sender_name}")
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        continue

                self.logger.info(f"Found {unread_count} unread messages")

            finally:
                self.logger.info("Closing browser...")
                browser.close()
                p.stop()
                self.logger.info("Browser closed")

        except PlaywrightTimeout as e:
            self.logger.error(f"Playwright timeout occurred")
            self.logger.error(f"Details: {e}")
        except Exception as e:
            self.logger.error(f"LinkedIn check failed: {type(e).__name__}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        return updates

    def get_item_id(self, item) -> str:
        """Get unique identifier for a LinkedIn item."""
        return f"{item['type']}_{item['id']}"

    def create_action_file(self, item) -> Path:
        """Create a task file in Needs_Action for the LinkedIn item."""
        # Use microseconds for unique filenames when processing multiple items
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:22]  # Trim to 22 chars

        if item['type'] == 'message':
            # Create safe filename for Inbox
            safe_sender = self._sanitize_filename(item['sender'])
            inbox_filename = f"LINKEDIN_MSG_{safe_sender}_{timestamp}.md"
            inbox_file = self.inbox / inbox_filename

            # Save FULL message to Inbox first
            inbox_content = f"""---
type: linkedin_message
source: LinkedInWatcher
created: {datetime.now().isoformat()}
message_id: {item['id']}
---

# LinkedIn Message from {item['sender']}

## Sender
{item['sender']}

## Message Preview
{item['preview']}

## Detected
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Full Message Content
> **Note:** This is a preview. View the full message on LinkedIn.
>
> Sender: {item['sender']}
> Preview: {item['preview']}

---
*Message ID: {item['id']}*
"""
            self.inbox.mkdir(parents=True, exist_ok=True)
            inbox_file.write_text(inbox_content)
            self.logger.info(f"Saved full message to Inbox: {inbox_filename}")

            # Create task file in Needs_Action that references Inbox
            task_file = self.needs_action / f"LINKEDIN_MSG_{timestamp}.md"

            content = f"""---
type: linkedin_message
source: LinkedInWatcher
created: {datetime.now().isoformat()}
status: pending
priority: medium
---

# LinkedIn Message: {item['sender']}

## Sender
{item['sender']}

## Preview
{item['preview']}

## Full Message
Read full message in [{inbox_filename}|Inbox/{inbox_filename}]

## Actions
- [ ] Read full message in [{inbox_filename}|Inbox/{inbox_filename}]
- [ ] Determine response needed
- [ ] Respond or archive

---
*Item ID: {item['id']}*
"""

            task_file.write_text(content)

        self._save_state()
        self.logger.info(f"Created LinkedIn task: {task_file.name}")

        return task_file

    def _sanitize_filename(self, text: str) -> str:
        """
        Remove problematic characters from filename.

        Args:
            text: String to sanitize

        Returns:
            Safe filename
        """
        # Remove or replace problematic chars
        text = text.replace('/', '_')
        text = text.replace('\\', '_')
        text = text.replace(':', '_')

        # Limit length
        if len(text) > 50:
            text = text[:47] + '...'

        return text

    def run(self):
        """Run the watcher using polling with error recovery."""
        self.logger.info(f"Starting LinkedInWatcher (polling mode)")
        self.logger.info(f"Session: {self.session_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("")
        self.logger.info("=" * 50)
        self.logger.info("Monitoring LinkedIn for:")
        self.logger.info("  - New messages")
        self.logger.info("  - Connection requests")
        self.logger.info("=" * 50)

        # First run notification
        if self.first_run:
            self.logger.info("")
            self.logger.info("=" * 50)
            self.logger.info("FIRST RUN DETECTED!")
            self.logger.info("Browser will open for LinkedIn authentication.")
            self.logger.info("Please log in - session will be saved for future runs.")
            self.logger.info("=" * 50)
            self.logger.info("")

        # Use parent class run() with error recovery
        super().run()


def main():
    """Entry point for running the watcher directly."""
    import sys

    # Default vault path
    vault_path = Path(__file__).parent.parent.parent / "AI_Employee_Vault"

    # Allow command line override
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path not found: {vault_path}")
        print("Usage: python linkedin_watcher.py [vault_path]")
        sys.exit(1)

    try:
        watcher = LinkedInWatcher(str(vault_path))
        watcher.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n⚠️  LinkedIn Watcher requires Playwright setup.")
        print("\nFirst run setup:")
        print("1. Run: uv run python watchers/linkedin_watcher.py")
        print("2. Log in to LinkedIn when browser opens")
        print("3. Session will be saved for future runs")
        sys.exit(1)


if __name__ == "__main__":
    main()
