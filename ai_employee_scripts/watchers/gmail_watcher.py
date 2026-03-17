"""
Gmail Watcher - Monitors Gmail for new emails and creates action items

Monitors Gmail for unread/important emails and creates tasks in AI Employee vault.

Usage:
    python gmail_watcher.py
"""

import os
import time
import logging
from pathlib import Path
from typing import List
from datetime import datetime
import base64
import email
from email.policy import default
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to import error_recovery
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_watcher import BaseWatcher
from error_recovery import with_retry, CircuitBreaker, is_transient_error
from shared.dedup_client import DedupClient


# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Gmail Watcher - monitors Gmail for new emails.

    Requires OAuth credentials (credentials.json) for authentication.
    First run will open browser for OAuth flow and save token.json
    """

    def __init__(self, vault_path: str, credentials_path: str = None, check_interval: int = 120,
                 dedup_api_url: str = None):
        """
        Initialize Gmail Watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            credentials_path: Path to credentials.json (OAuth client secrets)
            check_interval: Seconds between checks (default: 120)
            dedup_api_url: URL of dedup API server for cloud coordination (optional)
        """
        super().__init__(vault_path, check_interval)
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self.service = None
        self.processed_ids = set()
        self._load_processed_ids()

        # Add Inbox path for storing full emails
        self.inbox = self.vault_path / "Inbox"

        # Initialize dedup client for cloud coordination
        json_path = self.vault_path / "Logs" / "gmail_processed_ids.json"
        self.dedup_client = DedupClient(
            api_url=dedup_api_url,
            json_path=json_path,
            source="local"
        )
        if dedup_api_url:
            self.logger.info(f"Dedup API enabled: {dedup_api_url}")

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        # Look for credentials in script directory or parent directory
        if self.credentials_path is None:
            # Try default locations
            script_dir = Path(__file__).parent.parent
            possible_paths = [
                script_dir / 'credentials.json',
                script_dir.parent / 'credentials.json',
                script_dir.parent / 'ai_employee_scripts' / 'credentials.json',
            ]
            for path in possible_paths:
                if path.exists():
                    self.credentials_path = path
                    break
            else:
                self.logger.error(f"credentials.json not found at {self.credentials_path}")
                self.logger.error("Please download from Google Cloud Console and place in ai_employee_scripts/")
                raise FileNotFoundError("credentials.json not found")

        # Look for token file
        token_path = self.credentials_path.parent / 'token_gmail.json'

        creds = None
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
                if creds and creds.valid:
                    self.logger.info("Using existing valid credentials")
                    self.service = build('gmail', 'v1', credentials=creds)
                    return
                else:
                    self.logger.info("Existing credentials expired, refreshing...")
                    try:
                        creds.refresh(Request())
                        # Build service after refresh
                        self.service = build('gmail', 'v1', credentials=creds)
                        self.logger.info("Gmail authentication complete")
                        return
                    except Exception as e:
                        self.logger.warning(f"Refresh failed: {e}, need to re-authenticate")
                        # Fall through to OAuth flow
                        creds = None
            except Exception as e:
                self.logger.warning(f"Could not load existing token: {e}")

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            self.logger.info("No valid credentials found, starting OAuth flow...")
            self.logger.info("Waiting for authorization on http://localhost:8080")
            self.logger.info("Open this URL in your browser (WSL users: use Windows browser):")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )

                # Generate and print the authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')

                self.logger.info("")
                self.logger.info("=" * 60)
                self.logger.info("Open this URL in your Windows browser:")
                self.logger.info("=" * 60)
                self.logger.info(auth_url)
                self.logger.info("=" * 60)
                self.logger.info("")

                # Run local server flow - use static port for WSL
                creds = flow.run_local_server(
                    port=8080,
                    open_browser=False  # We'll provide the URL manually
                )

                # Save credentials for next run
                token_path = self.credentials_path.parent / 'token_gmail.json'
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

                self.service = build('gmail', 'v1', credentials=creds)
                self.logger.info("Gmail OAuth successful! Credentials saved.")

            except Exception as e:
                self.logger.error(f"OAuth flow failed: {e}")
                raise

        self.logger.info("Gmail authentication complete")

    def _load_processed_ids(self):
        """Load previously processed message IDs."""
        state_file = self.vault_path / "Logs" / "gmail_processed_ids.txt"
        if state_file.exists():
            self.processed_ids = set(state_file.read_text().strip().split('\n'))

    def _save_processed_ids(self):
        """Save processed message IDs to state file and sync with API."""
        # Save to local txt file (legacy, kept for compatibility)
        state_file = self.vault_path / "Logs"
        state_file.mkdir(parents=True, exist_ok=True)
        txt_file = state_file / "gmail_processed_ids.txt"
        txt_file.write_text('\n'.join(self.processed_ids))

    def _is_already_processed(self, message_id: str) -> bool:
        """
        Check if message was already processed using two-layer deduplication.

        Layer 1: Check local processed_ids set (in-memory, from txt file)
        Layer 2: Check via dedup client (JSON + API for cloud coordination)

        Args:
            message_id: Gmail message ID to check

        Returns:
            True if already processed, False if new
        """
        # Layer 1: Check local in-memory set
        if message_id in self.processed_ids:
            return True

        # Layer 2: Check via dedup client (JSON + API)
        if self.dedup_client.is_processed(message_id):
            self.logger.info(f"Message {message_id} found via dedup client (cloud processed)")
            return True

        return False

    def _register_processed(self, message_id: str):
        """
        Register a message as processed using two-layer storage.

        Layer 1: Add to local processed_ids set and save to txt file
        Layer 2: Register via dedup client (JSON + API for cloud coordination)

        Args:
            message_id: Gmail message ID to register
        """
        # Layer 1: Add to local set and save
        self.processed_ids.add(message_id)
        self._save_processed_ids()

        # Layer 2: Register via dedup client (JSON + API)
        self.dedup_client.register(message_id)

    @with_retry(max_attempts=3, base_delay=2, backoff_factor=2)
    def check_for_updates(self) -> list:
        """
        Check for new unread important emails.

        With automatic retry on transient failures.

        Returns:
            List of new email messages
        """
        results = self.service.users().messages().list(
            userId='me',
            q='newer_than:1d -in:sent',
            maxResults=20
        ).execute()

        messages = results.get('messages', [])

        # Filter out already processed messages using two-layer deduplication
        new_messages = [
            m for m in messages
            if not self._is_already_processed(m['id'])
        ]

        return new_messages

    def get_item_id(self, item) -> str:
        """Get unique identifier for an email message."""
        return item['id']

    def _get_email_body(self, payload) -> str:
        """
        Extract email body from Gmail payload.

        Args:
            payload: Gmail message payload

        Returns:
            Decoded email body as string
        """
        body = ""

        # Check if body is in 'body' directly
        if 'body' in payload and 'data' in payload['body']:
            body = payload['body']['data']
        # Check for multipart (parts)
        elif 'parts' in payload:
            for part in payload['parts']:
                # Recursively check nested parts
                if 'parts' in part:
                    body = body + self._get_email_body(part)
                elif 'body' in part and 'data' in part['body']:
                    body = body + part['body']['data']

        # Decode base64
        if body:
            try:
                body = base64.urlsafe_b64decode(body).decode('utf-8', errors='ignore')
            except Exception as e:
                self.logger.warning(f"Error decoding email body: {e}")
                return ""

        return body

    def create_action_file(self, message) -> Path:
        """
        Create a task file in Needs_Action for an email.

        Args:
            message: Gmail message object

        Returns:
            Path to created action file
        """
        try:
            # Get FULL message details (not just metadata)
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'  # Changed from 'metadata' to 'full'
            ).execute()

            # Extract headers
            headers = {}
            for h in msg['payload'].get('headers', []):
                name = h['name']
                if name in ['From', 'Subject', 'Date', 'To', 'Cc']:
                    headers[name] = h['value']

            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', '')
            date_str = headers.get('Date', datetime.now().isoformat())
            to = headers.get('To', '')
            cc = headers.get('Cc', '')

            # Get full email body
            email_body = self._get_email_body(msg['payload'])
            snippet = msg.get('snippet', '')

            # Determine priority based on sender/subject
            priority = self._determine_priority(sender, subject)

            # Create safe filename
            safe_subject = self._sanitize_filename(subject)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Save FULL email to Inbox first
            inbox_filename = f"EMAIL_{safe_subject}_{timestamp}.md"
            inbox_file = self.inbox / inbox_filename

            inbox_content = f"""---
type: email
source: GmailWatcher
created: {datetime.now().isoformat()}
message_id: {message['id']}
---

# {subject or '(No Subject)'}

## From
{sender}

## To
{to}

## Cc
{cc}

## Date
{date_str}

## Body
{email_body}

---
*Email ID: {message['id']}*
"""
            self.inbox.mkdir(parents=True, exist_ok=True)
            inbox_file.write_text(inbox_content)

            # Create task file in Needs_Action that references Inbox file
            task_filename = f"TASK_EMAIL_{safe_subject}_{timestamp}.md"
            task_file = self.needs_action / task_filename

            content = f"""---
type: email
source: GmailWatcher
created: {datetime.now().isoformat()}
status: pending
priority: {priority}
message_id: {message['id']}
original_file: {inbox_filename}
---

# Email: {subject or '(No Subject)'}

## From
{sender}

## Date
{date_str}

## Subject
{subject}

## Preview
{snippet}

## Actions
- [ ] Read full email in [{inbox_filename}|Inbox/{inbox_filename}]
- [ ] Determine if action needed
- [ ] Draft reply or take action
- [ ] Move to Done when handled

---
*Email ID: {message['id']}*
"""

            task_file.write_text(content)

            # Mark as processed (two-layer: local + cloud coordination)
            self._register_processed(message['id'])

            self.logger.info(f"Saved email to Inbox: {inbox_filename}")
            self.logger.info(f"Created email task: {task_file.name}")

            return task_file

        except HttpError as error:
            self.logger.error(f"Error fetching message {message['id']}: {error}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None

    def _determine_priority(self, sender: str, subject: str) -> str:
        """
        Determine email priority based on sender and subject.

        Args:
            sender: Email sender address
            subject: Email subject line

        Returns:
            Priority level: high, medium, or low
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()

        # High priority keywords
        high_keywords = ['urgent', 'asap', 'emergency', 'important', 'deadline']
        if any(kw in subject_lower for kw in high_keywords):
            return 'high'

        # High priority senders (customize based on your contacts)
        # Add important clients, boss, etc.
        # if any(contact in sender_lower for contact in self.high_priority_contacts):
        #     return 'high'

        # Medium priority
        medium_keywords = ['invoice', 'payment', 'meeting', 'proposal']
        if any(kw in subject_lower for kw in medium_keywords):
            return 'medium'

        return 'low'

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
        """
        Run the watcher using polling with error recovery.

        Checks for new emails every 2 minutes.
        Uses base class run() which includes retry, circuit breaker, and dead letter queue.
        """
        self.logger.info("Starting Gmail Watcher (polling mode)")
        self.logger.info(f"Credentials: {self.credentials_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("")

        # Authenticate first before starting the loop
        self._authenticate()

        # Use parent class run() with error recovery
        super().run()


def main():
    """Entry point for running the watcher directly."""
    import sys
    import os

    # Default vault path (go up from watchers/ to project root, then into AI_Employee_Vault)
    vault_path = Path(__file__).parent.parent.parent / "AI_Employee_Vault"

    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path not found: {vault_path}")
        print("Usage: python gmail_watcher.py [vault_path]")
        sys.exit(1)

    # Read dedup API URL from environment variable (optional)
    dedup_api_url = os.getenv("DEDUP_API_URL")

    try:
        watcher = GmailWatcher(
            vault_path=str(vault_path),
            dedup_api_url=dedup_api_url
        )
        watcher.run()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n⚠️  Gmail credentials not found!")
        print("\nTo set up Gmail API:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a project and enable Gmail API")
        print("3. Download credentials.json to this directory")
        print("\nFor detailed instructions, see:")
        print("https://developers.google.com/gmail/api/quickstart/python")
        sys.exit(1)


if __name__ == "__main__":
    main()
