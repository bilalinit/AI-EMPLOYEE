#!/usr/bin/env python3
"""
LinkedIn API MCP Server for AI Employee

This server uses the LinkedIn Share API (v2/ugcPosts) to post content
to LinkedIn using an OAuth 2.0 access token.

Environment variables required:
  - LINKEDIN_ACCESS_TOKEN: Your LinkedIn OAuth 2.0 access token
  - LINKEDIN_CLIENT_ID: Your LinkedIn application client ID
  - LINKEDIN_CLIENT_SECRET: Your LinkedIn application client secret

Usage:
  uv run python mcp_servers/linkedin_api_mcp.py
"""

import sys
import os
from pathlib import Path
from typing import Any

# MCP imports
from mcp.server.fastmcp import FastMCP

# HTTP client imports
import httpx

# =============================================================================
# CONFIGURATION
# =============================================================================

# LinkedIn API endpoints
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_UGC_POSTS_ENDPOINT = f"{LINKEDIN_API_BASE}/ugcPosts"
# Use OpenID Connect userinfo endpoint for profile
LINKEDIN_PROFILE_ENDPOINT = f"{LINKEDIN_API_BASE}/userinfo"

# File locations
SCRIPT_DIR = Path(__file__).parent.parent
ENV_FILE = SCRIPT_DIR / '.env'

# =============================================================================
# ENVIRONMENT & AUTHENTICATION
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

# Load .env file at module import
_load_env_file()

def print_status(message: str, emoji: str = "✅"):
    """Print status message to stderr (safe for MCP stdio transport)."""
    print(f"{emoji} {message}", file=sys.stderr, flush=True)


def get_access_token() -> str:
    """
    Get LinkedIn access token from environment.

    Returns:
        Access token string

    Raises:
        ValueError: If access token not found in environment
    """
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        print_status("LINKEDIN_ACCESS_TOKEN not found in environment!", "❌")
        print_status("", "")
        print_status("To set up LinkedIn API access:", "📝")
        print_status("1. Create a LinkedIn application at https://www.linkedin.com/developers/tools", "1️⃣")
        print_status("2. Add 'Share on LinkedIn' and 'Identity' permissions", "2️⃣")
        print_status("3. Get your OAuth 2.0 access token", "3️⃣")
        print_status("4. Add LINKEDIN_ACCESS_TOKEN to your .env file", "4️⃣")
        print_status("", "")
        print_status("For detailed instructions, see:", "📖")
        print_status("https://learn.microsoft.com/en-us/linkedin/marketing/community-management/ugc-posts", "🔗")
        raise ValueError("LINKEDIN_ACCESS_TOKEN not found in environment")

    return token


def get_http_client() -> httpx.AsyncClient:
    """
    Get an async HTTP client for LinkedIn API calls.

    Returns:
        httpx.AsyncClient instance configured for LinkedIn API
    """
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202501"
    }
    return httpx.AsyncClient(headers=headers, timeout=30.0)


# =============================================================================
# MCP SERVER
# =============================================================================

# Initialize FastMCP server
mcp = FastMCP(
    "linkedin-api",
    instructions="LinkedIn API operations: post content to LinkedIn, get profile information"
)


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
async def post_to_linkedin(text: str, title: str = "") -> str:
    """Post text content to LinkedIn using the LinkedIn Share API.

    Args:
        text: The post content (max 3000 characters for LinkedIn articles)
        title: Optional title/headline for the post

    Returns:
        Success message with post ID or error details
    """
    print_status(f"Posting to LinkedIn...", "📝")

    client = None
    try:
        # First, get the user's profile ID (URN)
        client = get_http_client()
        profile_response = await client.get(LINKEDIN_PROFILE_ENDPOINT)

        if profile_response.status_code != 200:
            error_detail = profile_response.text
            print_status(f"Failed to get profile: {profile_response.status_code}", "❌")
            return f"Error: Could not retrieve LinkedIn profile. Status: {profile_response.status_code}, Details: {error_detail}"

        profile_data = profile_response.json()
        # OpenID Connect uses 'sub' for subject/person ID, REST API used 'id'
        person_urn = profile_data.get("sub") or profile_data.get("id")

        if not person_urn:
            print_status("No person URN found in profile response", "❌")
            return f"Error: No person ID found in profile response. Data: {profile_data}"

        print_status(f"Got profile URN: {person_urn}", "👤")

        # Prepare the post content
        # Combine title and text if title is provided
        post_content = text
        if title:
            post_content = f"{title}\n\n{text}"

        # Truncate if too long (LinkedIn has limits)
        if len(post_content) > 3000:
            post_content = post_content[:2997] + "..."
            print_status("Post content truncated to 3000 characters", "⚠️")

        # Build the UGC post request body
        post_body = {
            "author": f"urn:li:person:{person_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Post to LinkedIn
        print_status("Sending post to LinkedIn API...", "📤")
        post_response = await client.post(
            LINKEDIN_UGC_POSTS_ENDPOINT,
            json=post_body
        )

        if post_response.status_code in [200, 201]:
            response_data = post_response.json()
            post_urn = response_data.get("id", "unknown")
            print_status(f"Post published successfully! URN: {post_urn}", "✅")
            return f"""Post published successfully!

Post URN: {post_urn}
Content: {post_content[:200]}{'...' if len(post_content) > 200 else ''}

Timestamp: {response_data.get('created', {}).get('time', 'N/A')}
"""
        else:
            error_detail = post_response.text
            print_status(f"Failed to post: {post_response.status_code}", "❌")
            return f"Error: Failed to post to LinkedIn. Status: {post_response.status_code}, Details: {error_detail}"

    except httpx.TimeoutException:
        error_msg = "Request timed out. LinkedIn API is taking too long to respond."
        print_status(error_msg, "❌")
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
        print_status(error_msg, "❌")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg
    finally:
        if client:
            await client.aclose()


@mcp.tool()
async def get_linkedin_profile() -> str:
    """Fetch the authenticated user's basic LinkedIn profile.

    Returns:
        User profile information including ID, name, and other details
    """
    print_status("Fetching LinkedIn profile...", "👤")

    client = None
    try:
        client = get_http_client()
        response = await client.get(LINKEDIN_PROFILE_ENDPOINT)

        if response.status_code != 200:
            error_detail = response.text
            print_status(f"Failed to get profile: {response.status_code}", "❌")
            return f"Error: Could not retrieve LinkedIn profile. Status: {response.status_code}, Details: {error_detail}"

        profile_data = response.json()
        print_status("Profile retrieved successfully", "✅")

        # Extract relevant profile information
        # OpenID Connect uses 'sub' for subject/person ID, REST API used 'id'
        person_urn = profile_data.get("sub") or profile_data.get("id", "")
        # OpenID Connect uses 'given_name' and 'family_name', REST API used 'localizedFirstName' and 'localizedLastName'
        first_name = profile_data.get("given_name") or profile_data.get("localizedFirstName", "")
        last_name = profile_data.get("family_name") or profile_data.get("localizedLastName", "")
        email = profile_data.get("email", "")

        result = f"""LinkedIn Profile Information:

Name: {first_name} {last_name}
Email: {email}
Person URN: {person_urn}

Full Profile Data:
{profile_data}

Note: Use the Person URN (without 'urn:li:person:' prefix) as the author URN for posting.
"""
        return result

    except httpx.TimeoutException:
        error_msg = "Request timed out. LinkedIn API is taking too long to respond."
        print_status(error_msg, "❌")
        return error_msg
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
        print_status(error_msg, "❌")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return error_msg
    finally:
        if client:
            await client.aclose()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Run the LinkedIn API MCP server."""
    print_status("", "")
    print_status("╔════════════════════════════════════════════════════════╗", "🔗")
    print_status("║      LinkedIn API MCP Server for AI Employee           ║", "🤖")
    print_status("╚════════════════════════════════════════════════════════╝", "🔗")
    print_status("", "")

    # Verify access token is available
    try:
        token = get_access_token()
        print_status(f"Access token found: {token[:20]}...", "🔑")
        print_status("", "")
    except ValueError as e:
        print_status("", "")
        print_status(f"Setup incomplete: {e}", "⚠️")
        print_status("", "")
        return

    print_status("Starting MCP server...", "🚀")
    print_status("Tools available: post_to_linkedin, get_linkedin_profile", "🛠️")
    print_status("", "")
    print_status("Server is running. Press Ctrl+C to stop.", "⏳")
    print_status("", "")

    try:
        # Start MCP server
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        print_status("", "")
        print_status("LinkedIn API MCP Server stopped by user", "👋")
    except Exception as e:
        print_status("", "")
        print_status(f"Fatal error: {e}", "❌")
        raise


if __name__ == "__main__":
    main()
