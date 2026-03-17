"""
Shared utilities for AI Employee watchers.

This package contains components shared between local and cloud watchers.
"""

from .dedup_client import DedupClient

__all__ = ["DedupClient"]