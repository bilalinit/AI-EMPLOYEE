#!/usr/bin/env python3
"""
Twitter/X API MCP Server for AI Employee

This server uses the Twitter API v2 via Tweepy to post tweets
using OAuth 1.0a authentication (4-key method).

Environment variables required:
  - X_API_KEY: Your Twitter/X API Key (Consumer Key)
  - X_API_SECRET: Your Twitter/X API Secret (Consumer Secret)
  - X_ACCESS_TOKEN: Your Twitter/X Access Token
  - X_ACCESS_TOKEN_SECRET: Your Twitter/X Access Token Secret

Usage:
  uv run python mcp_servers/twitter_mcp.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Any

# MCP imports
from mcp.server.fastmcp import FastMCP

# Twitter imports
import tweepy

# =============================================================================
# CONFIGURATION
# =============================================================================

# File locations
SCRIPT_DIR = Path(__file__).parent.parent
ENV_FILE = SCRIPT_DIR / '.env'

# Tweet character limit
TWEET_MAX_CHARS = 280

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


def get_twitter_client() -> tweepy.Client:
    """
    Initialize and return a Tweepy v2 Client using OAuth 1.0a credentials.

    Returns:
        tweepy.Client instance ready to post tweets

    Raises:
        ValueError: If any required credentials are missing
    """
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    missing = []
    if not api_key:
        missing.append("X_API_KEY")
    if not api_secret:
        missing.append("X_API_SECRET")
    if not access_token:
        missing.append("X_ACCESS_TOKEN")
    if not access_token_secret:
        missing.append("X_ACCESS_TOKEN_SECRET")

    if missing:
        print_status(f"Missing credentials: {', '.join(missing)}", "❌")
        print_status("Add these to your .env file:", "📝")
        for key in missing:
            print_status(f"  {key}=your_value_here", "  ")
        raise ValueError(f"Missing Twitter credentials: {', '.join(missing)}")

    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )


# =============================================================================
# MCP SERVER
# =============================================================================

# Initialize FastMCP server
mcp = FastMCP(
    "twitter-api",
    instructions="Twitter/X API operations: post tweets, get profile information for the AI Employee"
)


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
def post_tweet(text: str) -> str:
    """Post a tweet to Twitter/X on behalf of the authenticated account.

    Args:
        text: The tweet content (max 280 characters). Will be truncated if too long.

    Returns:
        Success message with tweet URL or error details
    """
    print_status(f"Preparing to post tweet...", "📝")

    try:
        client = get_twitter_client()

        # Truncate if over limit
        if len(text) > TWEET_MAX_CHARS:
            text = text[:TWEET_MAX_CHARS - 3] + "..."
            print_status(f"Tweet truncated to {TWEET_MAX_CHARS} characters", "⚠️")

        print_status(f"Posting tweet ({len(text)} chars)...", "📤")

        # Post the tweet using OAuth 1.0a (user_auth=True is default)
        response = client.create_tweet(text=text)

        if response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
            print_status(f"Tweet posted successfully! ID: {tweet_id}", "✅")

            return f"""Tweet posted successfully!

Tweet ID: {tweet_id}
URL: {tweet_url}
Content: {text}
Posted at: {datetime.now().isoformat()}
"""
        else:
            return "Error: Tweet was not posted. No data returned from Twitter API."

    except tweepy.errors.Forbidden as e:
        error_msg = (
            f"Forbidden (403): Twitter rejected the request.\n"
            f"Most likely cause: Access Token is 'Read Only' — you need 'Read and Write'.\n"
            f"Fix: Go to developer.x.com → Your App → User authentication settings → "
            f"Set permissions to 'Read and Write' → Regenerate your Access Token.\n"
            f"Details: {e}"
        )
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"

    except tweepy.errors.Unauthorized as e:
        error_msg = (
            f"Unauthorized (401): Invalid credentials.\n"
            f"Check that your X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, "
            f"X_ACCESS_TOKEN_SECRET are all correct in your .env file.\n"
            f"Details: {e}"
        )
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"

    except tweepy.errors.TooManyRequests as e:
        error_msg = (
            f"Rate limit exceeded (429): Too many requests.\n"
            f"Free tier allows 500 posts per month. Wait before trying again.\n"
            f"Details: {e}"
        )
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"

    except tweepy.errors.TweepyException as e:
        error_msg = f"Twitter API error: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"


@mcp.tool()
def get_twitter_profile() -> str:
    """Fetch the authenticated user's Twitter/X profile information.

    Returns:
        Profile information including username, name, and account ID
    """
    print_status("Fetching Twitter/X profile...", "👤")

    try:
        client = get_twitter_client()

        # get_me() returns the authenticated user's profile
        response = client.get_me(
            user_fields=["name", "username", "description", "public_metrics"]
        )

        if response.data:
            user = response.data
            metrics = user.public_metrics if hasattr(user, 'public_metrics') and user.public_metrics else {}

            print_status(f"Profile retrieved: @{user.username}", "✅")

            return f"""Twitter/X Profile Information:

Name: {user.name}
Username: @{user.username}
User ID: {user.id}
Bio: {getattr(user, 'description', 'N/A')}

Public Metrics:
  Followers: {metrics.get('followers_count', 'N/A')}
  Following: {metrics.get('following_count', 'N/A')}
  Tweets: {metrics.get('tweet_count', 'N/A')}

Profile URL: https://twitter.com/{user.username}
"""
        else:
            return "Error: Could not retrieve profile. No data returned."

    except tweepy.errors.Unauthorized as e:
        error_msg = f"Unauthorized (401): Check your credentials in .env file.\nDetails: {e}"
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"

    except tweepy.errors.TweepyException as e:
        error_msg = f"Twitter API error: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {e}"
        print_status(error_msg, "❌")
        return f"Error: {error_msg}"


@mcp.tool()
def post_business_update(
    update_type: str,
    details: str,
    hashtags: str = ""
) -> str:
    """Post a formatted business update tweet for the AI Employee workflow.

    This tool formats common business events into professional tweets
    automatically, so Claude doesn't need to manually format every tweet.

    Args:
        update_type: Type of update. Options:
                     'invoice_sent' - Invoice sent to client
                     'project_complete' - Project delivered
                     'new_service' - Announcing a new service
                     'milestone' - Business milestone reached
                     'general' - General business update
        details: The specific details of the update (e.g. "delivered video editing project for Client A")
        hashtags: Optional hashtags to append (e.g. "#freelance #videoediting")

    Returns:
        Success message with tweet URL or error details
    """
    print_status(f"Formatting business update tweet: {update_type}", "📋")

    # Format tweet based on update type
    templates = {
        "invoice_sent": f"✅ Another project invoiced and delivered! {details}",
        "project_complete": f"🎉 Project complete! {details}",
        "new_service": f"🚀 Excited to announce: {details}",
        "milestone": f"🏆 Milestone reached: {details}",
        "general": details,
    }

    tweet_text = templates.get(update_type, details)

    # Add hashtags if provided
    if hashtags:
        candidate = f"{tweet_text}\n\n{hashtags}"
        # Only add hashtags if it still fits in 280 chars
        if len(candidate) <= TWEET_MAX_CHARS:
            tweet_text = candidate

    print_status(f"Formatted tweet: {tweet_text[:80]}...", "📝")

    # Reuse post_tweet for the actual posting
    return post_tweet(tweet_text)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Run the Twitter/X API MCP server."""
    print_status("", "")
    print_status("╔════════════════════════════════════════════════════════╗", "🐦")
    print_status("║      Twitter/X API MCP Server for AI Employee          ║", "🤖")
    print_status("╚════════════════════════════════════════════════════════╝", "🐦")
    print_status("", "")

    # Verify credentials are available at startup
    try:
        client = get_twitter_client()
        print_status("All 4 credentials found in .env", "🔑")
        print_status("", "")
    except ValueError as e:
        print_status(f"Setup incomplete: {e}", "⚠️")
        print_status("", "")
        return

    print_status("Starting MCP server...", "🚀")
    print_status("Tools available:", "🛠️")
    print_status("  - post_tweet: Post any text as a tweet", "  ")
    print_status("  - get_twitter_profile: Get your account info", "  ")
    print_status("  - post_business_update: Post formatted business updates", "  ")
    print_status("", "")
    print_status("Server is running. Press Ctrl+C to stop.", "⏳")
    print_status("", "")

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print_status("", "")
        print_status("Twitter/X API MCP Server stopped by user", "👋")
    except Exception as e:
        print_status(f"Fatal error: {e}", "❌")
        raise


if __name__ == "__main__":
    main()
