"""
Base Cloud Watcher - Template for all cloud watchers

Cloud watchers read credentials from .env instead of credentials.json.
They create the same file format as local watchers for compatibility.
"""
import os
import time
import logging
import traceback
import json
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

# Load .env file FIRST
from dotenv import load_dotenv
load_dotenv()


class BaseCloudWatcher(ABC):
    """Abstract base class for all cloud watchers."""

    def __init__(self, vault_path: str, check_interval: int = 120):
        # Resolve to absolute path to avoid issues with relative paths
        self.vault_path = Path(vault_path).resolve()
        self.needs_action = self.vault_path / 'Needs_Action'
        self.failed_queue = self.vault_path / 'Failed_Queue'
        self.logs = self.vault_path / 'Logs'
        self.inbox = self.vault_path / 'Inbox'

        # Ensure folders exist
        for folder in [self.needs_action, self.failed_queue, self.logs, self.inbox]:
            folder.mkdir(parents=True, exist_ok=True)

        self.check_interval = check_interval
        self.logger = self._setup_logger()
        self.running = False
        self.source = 'cloud'  # Tag files as coming from cloud

        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10

    def _setup_logger(self):
        """Set up logging for this watcher."""
        logger = logging.getLogger(f'Cloud{self.__class__.__name__}')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - [CLOUD-%(name)s] - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # File handler
            log_file = self.logs / f"cloud_{self.__class__.__name__.lower()}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass

    def _create_failed_queue_file(self, item, error: Exception, retry_count: int = 0):
        """Create a failed queue file when an action cannot be processed."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"FAILED_CLOUD_{self.__class__.__name__}_{timestamp}.md"
        failed_file = self.failed_queue / filename

        content = f"""# Failed Action - Cloud {self.__class__.__name__}

retry_count: {retry_count}
timestamp: {datetime.now().isoformat()}
watcher: cloud_{self.__class__.__name__}
source: cloud

## Error
{type(error).__name__}: {str(error)}

## Item Details
```
{str(item)}
```

## Traceback
```
{traceback.format_exc()}
```

## Notes
This action will be retried automatically. After 3 failed attempts,
it will be moved to the archived folder and a human review alert
will be created.
"""

        try:
            failed_file.write_text(content, encoding='utf-8')
            self.logger.info(f"Created failed queue file: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to create failed queue file: {e}")

    def run(self):
        """Main loop - continuously check for updates."""
        self.running = True
        self.logger.info(f'Starting Cloud {self.__class__.__name__}...')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        self.logger.info(f'Source tag: {self.source}')

        try:
            while self.running:
                try:
                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f'Created: {filepath.name}')
                                self.consecutive_errors = 0
                            except Exception as e:
                                self.logger.error(f'Error creating action file: {e}')
                                self._create_failed_queue_file(item, e)

                except Exception as e:
                    self.consecutive_errors += 1
                    self.logger.error(f'Error in loop ({self.consecutive_errors}/{self.max_consecutive_errors}): {e}')

                    if self.consecutive_errors >= self.max_consecutive_errors:
                        self.logger.error(f'Too many consecutive errors, waiting 60s before retry')
                        time.sleep(60)

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Stopped by user')
            self.running = False
        except Exception as e:
            self.logger.error(f'Fatal error in Cloud {self.__class__.__name__}: {e}')
            self.logger.error(traceback.format_exc())
            raise

    def stop(self):
        """Stop the watcher."""
        self.running = False
