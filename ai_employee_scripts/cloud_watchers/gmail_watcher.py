"""
Cloud Gmail Watcher - Monitors Gmail using credentials from .env

Reads GOOGLE_CREDENTIALS from environment variable instead of credentials.json file.
Creates the same file format as local watcher for compatibility.
"""
import os
import json
import tempfile
import time
import base64
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Load .env file FIRST
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from cloud_watchers.base_cloud_watcher import BaseCloudWatcher
from shared.dedup_client import DedupClient


# Gmail API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]


class CloudGmailWatcher(BaseCloudWatcher):
    """Cloud-based Gmail watcher using .env credentials."""

    def __init__(self, vault_path: str, check_interval: int = 120, dedup_api_url: str = None):
        """
        Initialize Cloud Gmail Watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval: Seconds between checks (default: 120)
            dedup_api_url: URL of local dedup API (optional, for cloud coordination)
        """
        super().__init__(vault_path, check_interval)
        self.service = None
        self.processed_ids = set()
        self._load_processed_ids()  # Load processed IDs

        # Initialize dedup client for local/cloud coordination
        # Cloud watcher uses local API (http://localhost:5000) since API runs on cloud
        json_path = self.logs / "gmail_processed_ids.json"
        self.dedup_client = DedupClient(
            api_url=dedup_api_url,
            json_path=json_path,
            source="cloud"
        )
        if dedup_api_url:
            self.logger.info(f"Dedup API enabled: {dedup_api_url}")

        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using credentials from .env."""
        # Read credentials from environment variable
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            self.logger.error('GOOGLE_CREDENTIALS not found in environment variables')
            self.logger.error('Please set GOOGLE_CREDENTIALS in .env file')
            raise ValueError('GOOGLE_CREDENTIALS environment variable not set')

        try:
            # Parse JSON from environment variable
            credentials_data = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse GOOGLE_CREDENTIALS as JSON: {e}')
            raise ValueError('GOOGLE_CREDENTIALS must be valid JSON')

        # Write to temp file for OAuth flow (Google library requires file)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(credentials_data, f)
            temp_credentials_path = f.name

        try:
            # Token file for cloud watcher
            token_dir = Path(__file__).parent.parent / 'sessions'
            token_dir.mkdir(parents=True, exist_ok=True)
            token_path = token_dir / 'token_cloud_gmail_watcher.json'

            creds = None
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        with open(token_path, 'w') as token:
                            token.write(creds.to_json())
                    except RefreshError:
                        self.logger.warning('Token expired. Re-authenticating...')
                        creds = None

                if not creds or not creds.valid:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        temp_credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=8081)  # Different port to avoid conflict
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())

            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Cloud Gmail authentication successful')

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_credentials_path)
            except:
                pass

    def _load_processed_ids(self):
        """Load previously processed message IDs from gmail_processed_ids.txt."""
        state_file = self.logs / 'gmail_processed_ids.txt'
        if state_file.exists():
            try:
                content = state_file.read_text(encoding='utf-8')
                self.processed_ids = set(content.strip().split('\n')) if content.strip() else set()
                self.logger.info(f'Loaded {len(self.processed_ids)} processed message IDs')
            except Exception as e:
                self.logger.warning(f'Could not load processed IDs: {e}')
                self.processed_ids = set()

    def _save_processed_ids(self):
        """Save processed message IDs to gmail_processed_ids.txt."""
        state_file = self.logs / 'gmail_processed_ids.txt'
        try:
            state_file.write_text('\n'.join(self.processed_ids), encoding='utf-8')
        except Exception as e:
            self.logger.error(f'Could not save processed IDs: {e}')

    def _is_already_processed(self, message_id: str) -> bool:
        """
        Check if message was already processed using two-layer deduplication.

        Layer 1: Check local processed_ids set (in-memory, from txt file)
        Layer 2: Check via dedup client (JSON + API for local/cloud coordination)

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
            self.logger.info(f"Message {message_id} found via dedup client (local processed)")
            return True

        return False

    def _register_processed(self, message_id: str):
        """
        Register a message as processed using two-layer storage.

        Layer 1: Add to local processed_ids set and save to txt file
        Layer 2: Register via dedup client (JSON + API for local/cloud coordination)

        Args:
            message_id: Gmail message ID to register
        """
        # Layer 1: Add to local set and save
        self.processed_ids.add(message_id)
        self._save_processed_ids()

        # Layer 2: Register via dedup client (JSON + API)
        self.dedup_client.register(message_id)

    def check_for_updates(self) -> List[Dict]:
        """
        Check for new recent emails (last 24 hours).

        Returns:
            List of new email messages
        """
        try:
            # Query for recent emails (last 24 hours), exclude sent emails
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

        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
            return []

    def create_action_file(self, message: Dict) -> Path:
        """
        Create action file for an email.
        Creates same format as local watcher for compatibility.

        Args:
            message: Gmail message object

        Returns:
            Path to created action file
        """
        try:
            # Get FULL message details
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {}
            for h in msg['payload'].get('headers', []):
                name = h['name']
                if name in ['From', 'Subject', 'Date', 'To', 'Cc']:
                    headers[name] = h['value']

            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date_str = headers.get('Date', datetime.now().isoformat())
            to = headers.get('To', '')
            cc = headers.get('Cc', '')

            # Extract email body
            body_text, body_html = self._extract_body(msg['payload'])

            # Determine priority
            priority = self._determine_priority(sender, subject)

            # 1. Store full email in Inbox/
            inbox_filename = f'EMAIL_{message["id"]}.md'
            inbox_filepath = self.inbox / inbox_filename

            inbox_content = f'''---
type: email
source: gmail
source_location: cloud
message_id: {message['id']}
from: {sender}
to: {to}
cc: {cc}
subject: {subject}
received: {date_str}
---

# {subject}

**From:** {sender}
**To:** {to}
**Cc:** {cc}
**Date:** {date_str}
**Message ID:** {message['id']}
**Source:** Cloud

---

## Email Body

{body_text if body_text else body_html}
'''

            inbox_filepath.write_text(inbox_content, encoding='utf-8')
            self.logger.info(f'Stored full email in Inbox: {inbox_filename}')

            # 2. Create task file in Needs_Action/
            safe_subject = subject[:50].replace('/', '-').replace('\\', '-')
            safe_subject = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in safe_subject)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            task_filename = f'EMAIL_{safe_subject}_{timestamp}.md'  # Same prefix as local watcher

            task_content = f'''---
type: email
source: gmail
source_location: cloud
message_id: {message['id']}
from: {sender}
subject: {subject}
received: {date_str}
priority: {priority}
status: pending
inbox_ref: {inbox_filename}
created: {datetime.now().isoformat()}
---

# Email from {sender}

## Subject
{subject}

## Details
- **From:** {sender}
- **Received:** {date_str}
- **Priority:** {priority}
- **Source:** Cloud Watcher
- **Full Email:** `../Inbox/{inbox_filename}`

## Preview
{body_text[:500] if body_text and len(body_text) > 500 else (body_text or body_html[:500] if body_html else '')}
{'...' if (body_text and len(body_text) > 500) or (body_html and len(body_html) > 500) else ''}

## Suggested Actions
- [ ] Read full email in `Inbox/{inbox_filename}`
- [ ] Determine if action needed
- [ ] Respond or archive

## Quick Reply Ideas
- [ ] "Thank you for reaching out..."
- [ ] "I'll review and get back to you..."
- [ ] Forward to relevant person
'''

            # Write to Needs_Action
            task_filepath = self.needs_action / task_filename
            task_filepath.write_text(task_content, encoding='utf-8')

            # Mark as processed (two-layer: local + cloud coordination)
            self._register_processed(message['id'])

            return task_filepath

        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')
            raise

    def _extract_body(self, payload: dict) -> tuple:
        """Extract email body from Gmail payload."""
        text_body = ''
        html_body = ''

        def decode_data(data: str) -> str:
            """Decode base64 URL encoded data."""
            if not data:
                return ''
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            try:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            except Exception:
                return data

        def extract_from_part(part: dict) -> tuple:
            """Recursively extract body from a message part."""
            text = ''
            html = ''

            if 'body' in part and 'data' in part['body']:
                data = decode_data(part['body']['data'])
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/plain':
                    text = data
                elif mime_type == 'text/html':
                    html = data

            if 'parts' in part:
                for subpart in part['parts']:
                    sub_text, sub_html = extract_from_part(subpart)
                    if sub_text and not text:
                        text = sub_text
                    if sub_html and not html:
                        html = sub_html

            return text, html

        text_body, html_body = extract_from_part(payload)

        # If HTML only, strip tags for text preview
        if not text_body and html_body:
            text_body = re.sub(r'<[^>]+>', ' ', html_body)
            text_body = ' '.join(text_body.split())

        return text_body, html_body

    def _determine_priority(self, sender: str, subject: str) -> str:
        """Determine email priority based on sender and subject."""
        sender_lower = sender.lower()
        subject_lower = subject.lower()

        # High priority keywords
        high_keywords = ['urgent', 'asap', 'emergency', 'important', 'deadline']
        if any(kw in subject_lower for kw in high_keywords):
            return 'high'

        # Medium priority
        medium_keywords = ['invoice', 'payment', 'meeting', 'proposal']
        if any(kw in subject_lower for kw in medium_keywords):
            return 'medium'

        return 'low'


def main():
    """Run the Cloud Gmail Watcher."""
    import sys

    # Default vault path
    vault_path = Path(__file__).parent.parent.parent / 'AI_Employee_Vault'

    # Allow command line override
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path not found: {vault_path}")
        print("Usage: python gmail_watcher.py [vault_path]")
        sys.exit(1)

    # Read dedup API URL from environment variable (optional)
    # Cloud watcher uses localhost since API runs on same cloud VM
    dedup_api_url = os.getenv("DEDUP_API_URL", "http://localhost:5000")

    try:
        watcher = CloudGmailWatcher(
            vault_path=str(vault_path),
            check_interval=120,  # Check every 2 minutes
            dedup_api_url=dedup_api_url
        )

        print("Cloud Gmail Watcher starting... Press Ctrl+C to stop.")
        watcher.run()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
