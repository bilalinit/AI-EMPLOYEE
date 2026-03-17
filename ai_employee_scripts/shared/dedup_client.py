"""
Deduplication Client - Coordinates email processing between local and cloud watchers

Provides two-layer deduplication:
1. Layer 1: JSON file (local, git synced every 5 minutes, backup)
2. Layer 2: API + SQLite (real-time coordination)

Both local and cloud watchers use this same client to prevent duplicate processing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import httpx


class DedupClient:
    """
    Client for deduplication between local and cloud watchers.

    Usage:
        client = DedupClient(
            api_url="https://your-cloud-url:5000",
            json_path=Path("Logs/gmail_processed_ids.json"),
            source="local"  # or "cloud"
        )

        # Check before processing
        if not client.is_processed(email_id):
            # Process email...
            client.register(email_id)
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        json_path: Optional[Path] = None,
        source: str = "unknown",
        api_key: Optional[str] = None,
        timeout: int = 5
    ):
        """
        Initialize deduplication client.

        Args:
            api_url: URL of the dedup API server (e.g., "https://your-cloud:5000")
            json_path: Path to the JSON file for local storage
            source: Source identifier ("local" or "cloud")
            api_key: Optional API key for authentication
            timeout: API request timeout in seconds
        """
        self.api_url = api_url.rstrip('/') if api_url else None
        self.json_path = json_path
        self.source = source
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(f"DedupClient({source})")

        # In-memory cache of processed IDs from JSON
        self._processed_ids: Dict[str, Any] = {}
        self._load_json()

    def _load_json(self):
        """Load processed IDs from JSON file."""
        if not self.json_path or not self.json_path.exists():
            self._processed_ids = {"processed_ids": [], "last_updated": None}
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._processed_ids = json.load(f)
            self.logger.debug(
                f"Loaded {len(self._processed_ids.get('processed_ids', []))} IDs from JSON"
            )
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Could not load JSON file: {e}")
            self._processed_ids = {"processed_ids": [], "last_updated": None}

    def _save_json(self):
        """Save processed IDs to JSON file."""
        if not self.json_path:
            return

        try:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self._processed_ids["last_updated"] = datetime.now().isoformat()

            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self._processed_ids, f, indent=2)

            self.logger.debug("Saved processed IDs to JSON")
        except IOError as e:
            self.logger.error(f"Could not save JSON file: {e}")

    def _check_api(self, email_id: str) -> bool:
        """
        Check if email was processed via API (Layer 2).

        Returns:
            True if processed, False if not processed or API unavailable
        """
        if not self.api_url:
            return False

        try:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.api_url}/check",
                    params={"id": email_id},
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("processed", False)
                else:
                    self.logger.warning(
                        f"API check returned status {response.status_code}"
                    )
                    return False

        except httpx.TimeoutException:
            self.logger.warning(f"API timeout for {email_id}")
            return False
        except httpx.RequestError as e:
            self.logger.warning(f"API request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected API error: {e}")
            return False

    def _register_api(self, email_id: str) -> bool:
        """
        Register processed email via API (Layer 2).

        Returns:
            True on success, False on failure (graceful degradation)
        """
        if not self.api_url:
            return False

        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.api_url}/register",
                    json={
                        "email_id": email_id,
                        "source": self.source
                    },
                    headers=headers
                )

                if response.status_code == 200:
                    self.logger.debug(f"Registered {email_id} via API")
                    return True
                else:
                    self.logger.warning(
                        f"API register returned status {response.status_code}"
                    )
                    return False

        except httpx.TimeoutException:
            self.logger.warning(f"API timeout registering {email_id}")
            return False
        except httpx.RequestError as e:
            self.logger.warning(f"API request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected API error: {e}")
            return False

    def is_processed(self, email_id: str) -> bool:
        """
        Check if an email has already been processed.

        Two-layer check:
        1. Check local JSON (fast, always available)
        2. Check API (real-time coordination, may be unavailable)

        Args:
            email_id: Gmail message ID to check

        Returns:
            True if already processed, False if new
        """
        # Layer 1: Check JSON (always available)
        json_ids = self._processed_ids.get("processed_ids", [])
        if email_id in json_ids:
            self.logger.debug(f"{email_id} found in JSON (processed)")
            return True

        # Layer 2: Check API (real-time coordination)
        if self._check_api(email_id):
            self.logger.debug(f"{email_id} found via API (processed)")
            return True

        return False

    def register(self, email_id: str) -> bool:
        """
        Register an email as processed.

        Saves to both:
        1. JSON file (local backup, git synced)
        2. API (real-time coordination)

        Args:
            email_id: Gmail message ID to register

        Returns:
            True if at least one storage succeeded
        """
        success = False

        # Layer 1: Save to JSON
        json_ids = self._processed_ids.get("processed_ids", [])
        if email_id not in json_ids:
            json_ids.append(email_id)
            self._processed_ids["processed_ids"] = json_ids
            self._save_json()
            success = True
            self.logger.info(f"Registered {email_id} in JSON")

        # Layer 2: Register via API (immediate, don't wait for git sync)
        if self._register_api(email_id):
            success = True

        return success

    def sync_from_api(self) -> int:
        """
        Pull all processed IDs from API to local JSON.

        Useful for:
        - Initial startup (get IDs processed by other watcher)
        - Recovery after downtime

        Returns:
            Number of new IDs synced
        """
        if not self.api_url:
            self.logger.warning("No API URL configured, cannot sync")
            return 0

        try:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key

            with httpx.Client(timeout=self.timeout * 2) as client:
                response = client.get(
                    f"{self.api_url}/sync",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    api_ids = set(data.get("processed_ids", []))

                    json_ids = set(self._processed_ids.get("processed_ids", []))
                    new_ids = api_ids - json_ids

                    if new_ids:
                        self._processed_ids["processed_ids"] = list(json_ids | api_ids)
                        self._save_json()
                        self.logger.info(f"Synced {len(new_ids)} new IDs from API")

                    return len(new_ids)
                else:
                    self.logger.warning(f"API sync returned status {response.status_code}")
                    return 0

        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about processed IDs."""
        return {
            "json_count": len(self._processed_ids.get("processed_ids", [])),
            "json_last_updated": self._processed_ids.get("last_updated"),
            "api_url": self.api_url,
            "source": self.source
        }