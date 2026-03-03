#!/usr/bin/env python3
"""
Meta Graph API MCP Server for AI Employee

Handles posting to both Facebook Pages and Instagram Business accounts
using the Meta Graph API v21.0 with a long-lived access token.

Environment variables required:
  - META_ACCESS_TOKEN: Your long-lived Meta access token (60 days)
  - META_PAGE_ID: Your Facebook Page ID (found in Page settings)

Usage:
  uv run python mcp_servers/meta_mcp.py
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

import httpx
from mcp.server.fastmcp import FastMCP

# =============================================================================
# CONFIGURATION
# =============================================================================

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

SCRIPT_DIR = Path(__file__).parent.parent
ENV_FILE = SCRIPT_DIR / '.env'

# =============================================================================
# ENVIRONMENT LOADING
# =============================================================================

def _load_env_file():
    """Load environment variables from .env file if not already set."""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()

_load_env_file()


def print_status(message: str, emoji: str = "✅"):
    """Print status to stderr (safe for MCP stdio transport)."""
    print(f"{emoji} {message}", file=sys.stderr, flush=True)


def get_credentials() -> tuple[str, str]:
    """
    Get Meta credentials from environment.

    Returns:
        Tuple of (access_token, page_id)

    Raises:
        ValueError: If credentials are missing
    """
    token = os.getenv("META_ACCESS_TOKEN")
    page_id = os.getenv("META_PAGE_ID")

    missing = []
    if not token:
        missing.append("META_ACCESS_TOKEN")
    if not page_id:
        missing.append("META_PAGE_ID")

    if missing:
        print_status(f"Missing credentials: {', '.join(missing)}", "❌")
        raise ValueError(f"Missing Meta credentials: {', '.join(missing)}")

    return token, page_id


def get_http_client(access_token: str) -> httpx.Client:
    """Return a synchronous HTTP client with token as default param."""
    return httpx.Client(
        params={"access_token": access_token},
        timeout=30.0
    )


# =============================================================================
# MCP SERVER
# =============================================================================

mcp = FastMCP(
    "meta-api",
    instructions="Meta Graph API: post to Facebook Page and Instagram Business account for AI Employee"
)


# =============================================================================
# HELPER: GET INSTAGRAM BUSINESS ACCOUNT ID
# =============================================================================

def _get_instagram_account_id(client: httpx.Client, page_id: str) -> str | None:
    """
    Get the Instagram Business Account ID linked to a Facebook Page.

    Returns:
        Instagram account ID string or None if not found
    """
    response = client.get(
        f"{GRAPH_API_BASE}/{page_id}",
        params={"fields": "instagram_business_account"}
    )

    if response.status_code != 200:
        print_status(f"Failed to get Instagram account: {response.text}", "❌")
        return None

    data = response.json()
    ig_account = data.get("instagram_business_account", {})
    ig_id = ig_account.get("id")

    if not ig_id:
        print_status("No Instagram Business account linked to this Facebook Page", "⚠️")
        print_status("Make sure your Instagram account is connected in Page settings", "💡")

    return ig_id


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
def post_to_facebook(text: str) -> str:
    """Post a text update to your Facebook Page.

    Args:
        text: The post content to publish on Facebook

    Returns:
        Success message with post ID or error details
    """
    print_status("Posting to Facebook Page...", "📘")

    try:
        access_token, page_id = get_credentials()
        client = get_http_client(access_token)

        # First get the Page access token (needed for posting AS the page)
        page_token_response = client.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "access_token"}
        )

        if page_token_response.status_code != 200:
            return f"Error: Could not get Page access token. {page_token_response.text}"

        page_token = page_token_response.json().get("access_token")
        if not page_token:
            return "Error: No Page access token returned. Make sure pages_manage_posts permission is granted."

        # Post to the Facebook Page feed
        post_response = client.post(
            f"{GRAPH_API_BASE}/{page_id}/feed",
            params={"access_token": page_token},
            json={"message": text}
        )

        if post_response.status_code == 200:
            post_id = post_response.json().get("id", "unknown")
            print_status(f"Facebook post published! ID: {post_id}", "✅")
            return f"""Facebook post published successfully!

Post ID: {post_id}
Page ID: {page_id}
Content: {text[:200]}{'...' if len(text) > 200 else ''}
Posted at: {datetime.now().isoformat()}

View at: https://www.facebook.com/{page_id}/posts/{post_id.split('_')[-1]}
"""
        else:
            error = post_response.json().get("error", {})
            error_msg = error.get("message", post_response.text)
            print_status(f"Facebook post failed: {error_msg}", "❌")
            return f"Error posting to Facebook: {error_msg}"

    except ValueError as e:
        return f"Configuration error: {e}"
    except httpx.TimeoutException:
        return "Error: Request timed out. Meta API took too long to respond."
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def post_to_instagram(caption: str, image_url: str) -> str:
    """Post an image with caption to your Instagram Business account.

    Instagram requires a publicly accessible image URL.
    The image must be a JPEG or PNG hosted on a public server.

    Args:
        caption: The caption for the Instagram post (max 2200 characters)
        image_url: A publicly accessible URL to the image to post

    Returns:
        Success message with post ID or error details
    """
    print_status("Posting to Instagram...", "📸")

    try:
        access_token, page_id = get_credentials()
        client = get_http_client(access_token)

        # Step 1: Get Instagram Business Account ID
        ig_account_id = _get_instagram_account_id(client, page_id)
        if not ig_account_id:
            return (
                "Error: No Instagram Business account found linked to your Facebook Page.\n"
                "Fix: Go to your Facebook Page Settings → Instagram → Connect account"
            )

        print_status(f"Instagram Account ID: {ig_account_id}", "👤")

        # Step 2: Create media container
        print_status("Creating media container...", "📦")
        container_response = client.post(
            f"{GRAPH_API_BASE}/{ig_account_id}/media",
            json={
                "image_url": image_url,
                "caption": caption[:2200]  # Instagram caption limit
            }
        )

        if container_response.status_code != 200:
            error = container_response.json().get("error", {})
            error_msg = error.get("message", container_response.text)
            return f"Error creating media container: {error_msg}"

        creation_id = container_response.json().get("id")
        if not creation_id:
            return "Error: No creation ID returned from Instagram API."

        print_status(f"Media container created: {creation_id}", "✅")

        # Step 3: Wait for Instagram to process the container
        print_status("Waiting for Instagram to process media...", "⏳")
        max_retries = 10
        for attempt in range(max_retries):
            time.sleep(3)  # Wait 3 seconds between checks
            status_response = client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/media",
                params={"fields": "status_code", "ids": creation_id}
            )
            if status_response.status_code == 200:
                data = status_response.json().get("data", [])
                if data and data[0].get("status_code") == "FINISHED":
                    print_status("Media processed successfully", "✅")
                    break
                elif data and data[0].get("status_code") in ["ERROR", "EXPIRED"]:
                    return f"Error: Media processing failed with status {data[0].get('status_code')}"
            print_status(f"Waiting... ({attempt + 1}/{max_retries})", "⏳")
        else:
            print_status("Continuing anyway (may still process)", "⚠️")

        # Step 4: Publish the container
        print_status("Publishing to Instagram...", "📤")
        publish_response = client.post(
            f"{GRAPH_API_BASE}/{ig_account_id}/media_publish",
            json={"creation_id": creation_id}
        )

        if publish_response.status_code == 200:
            media_id = publish_response.json().get("id", "unknown")
            print_status(f"Instagram post published! ID: {media_id}", "✅")
            return f"""Instagram post published successfully!

Media ID: {media_id}
Caption: {caption[:200]}{'...' if len(caption) > 200 else ''}
Image URL: {image_url}
Posted at: {datetime.now().isoformat()}
"""
        else:
            error = publish_response.json().get("error", {})
            error_msg = error.get("message", publish_response.text)
            print_status(f"Instagram publish failed: {error_msg}", "❌")
            return f"Error publishing to Instagram: {error_msg}"

    except ValueError as e:
        return f"Configuration error: {e}"
    except httpx.TimeoutException:
        return "Error: Request timed out."
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def post_to_both(text: str, image_url: str = "", instagram_caption: str = "") -> str:
    """Post to both Facebook and Instagram simultaneously.

    For Facebook: posts as text only (image optional via URL in text).
    For Instagram: requires an image URL.

    Args:
        text: Text content for Facebook post
        image_url: Public image URL (required for Instagram, optional for Facebook)
        instagram_caption: Custom caption for Instagram (uses text if not provided)

    Returns:
        Combined results for both platforms
    """
    print_status("Posting to Facebook and Instagram...", "🌐")

    results = []

    # Post to Facebook
    fb_result = post_to_facebook(text)
    results.append(f"=== FACEBOOK ===\n{fb_result}")

    # Post to Instagram if image URL provided
    if image_url:
        caption = instagram_caption if instagram_caption else text
        ig_result = post_to_instagram(caption, image_url)
        results.append(f"=== INSTAGRAM ===\n{ig_result}")
    else:
        results.append("=== INSTAGRAM ===\nSkipped: No image URL provided. Instagram requires an image.")

    return "\n\n".join(results)


@mcp.tool()
def get_meta_profile() -> str:
    """Get your Facebook Page and linked Instagram account information.

    Returns:
        Profile info for both Facebook Page and Instagram account
    """
    print_status("Fetching Meta profile info...", "👤")

    try:
        access_token, page_id = get_credentials()
        client = get_http_client(access_token)

        # Get Facebook Page info
        page_response = client.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={"fields": "name,followers_count,fan_count,instagram_business_account"}
        )

        if page_response.status_code != 200:
            return f"Error: Could not get Page info. {page_response.text}"

        page_data = page_response.json()
        ig_account = page_data.get("instagram_business_account", {})
        ig_id = ig_account.get("id")

        result = f"""Meta Profile Information:

=== FACEBOOK PAGE ===
Page Name: {page_data.get('name', 'N/A')}
Page ID: {page_id}
Followers: {page_data.get('followers_count', 'N/A')}
Page Likes: {page_data.get('fan_count', 'N/A')}
"""

        # Get Instagram info if linked
        if ig_id:
            ig_response = client.get(
                f"{GRAPH_API_BASE}/{ig_id}",
                params={"fields": "username,followers_count,media_count,biography"}
            )

            if ig_response.status_code == 200:
                ig_data = ig_response.json()
                result += f"""
=== INSTAGRAM BUSINESS ACCOUNT ===
Username: @{ig_data.get('username', 'N/A')}
Instagram ID: {ig_id}
Followers: {ig_data.get('followers_count', 'N/A')}
Total Posts: {ig_data.get('media_count', 'N/A')}
Bio: {ig_data.get('biography', 'N/A')}
"""
        else:
            result += "\n=== INSTAGRAM ===\nNo Instagram Business account linked to this Page."

        print_status("Profile retrieved successfully", "✅")
        return result

    except ValueError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def get_page_id_helper() -> str:
    """Helper tool to find your Facebook Page ID.

    Run this if you don't know your META_PAGE_ID yet.
    It uses your access token to list all Pages you manage.

    Returns:
        List of Pages with their IDs
    """
    print_status("Finding your Facebook Pages...", "🔍")

    try:
        access_token = os.getenv("META_ACCESS_TOKEN")
        if not access_token:
            _load_env_file()
            access_token = os.getenv("META_ACCESS_TOKEN")

        if not access_token:
            return "Error: META_ACCESS_TOKEN not found in .env file"

        client = httpx.Client(timeout=30.0)
        response = client.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": access_token}
        )

        if response.status_code != 200:
            return f"Error: {response.text}"

        pages = response.json().get("data", [])

        if not pages:
            return "No Facebook Pages found. Make sure you have created a Facebook Page."

        result = "Your Facebook Pages:\n\n"
        for page in pages:
            result += f"Page Name: {page.get('name')}\n"
            result += f"Page ID: {page.get('id')}\n"
            result += f"Add to .env: META_PAGE_ID={page.get('id')}\n"
            result += "-" * 40 + "\n"

        return result

    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the Meta API MCP server."""
    print_status("", "")
    print_status("╔════════════════════════════════════════════════════════╗", "📘")
    print_status("║      Meta Graph API MCP Server for AI Employee         ║", "🤖")
    print_status("╚════════════════════════════════════════════════════════╝", "📘")
    print_status("", "")

    try:
        token, page_id = get_credentials()
        print_status(f"Access token found: {token[:20]}...", "🔑")
        print_status(f"Page ID: {page_id}", "📄")
        print_status("", "")
    except ValueError:
        print_status("⚠️  Missing credentials — run get_page_id_helper() first", "⚠️")
        print_status("   then add META_PAGE_ID to your .env file", "")
        print_status("", "")

    print_status("Starting MCP server...", "🚀")
    print_status("Tools available:", "🛠️")
    print_status("  - post_to_facebook: Post text to your Facebook Page", "  ")
    print_status("  - post_to_instagram: Post image+caption to Instagram", "  ")
    print_status("  - post_to_both: Post to Facebook and Instagram together", "  ")
    print_status("  - get_meta_profile: Get Page and Instagram account info", "  ")
    print_status("  - get_page_id_helper: Find your Facebook Page ID", "  ")
    print_status("", "")
    print_status("Server is running. Press Ctrl+C to stop.", "⏳")
    print_status("", "")

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print_status("Meta API MCP Server stopped by user", "👋")
    except Exception as e:
        print_status(f"Fatal error: {e}", "❌")
        raise


if __name__ == "__main__":
    main()
