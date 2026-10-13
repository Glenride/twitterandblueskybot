"""Track DM recipients to prevent duplicate sends."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)


class DMTracker:
    """Tracks which recipients have already received DMs to prevent duplicates."""
    
    def __init__(self, tracking_file: Path):
        self.tracking_file = tracking_file
        self._sent_recipients: Set[str] = set()
        self._load()
    
    def _load(self) -> None:
        """Load previously sent recipients from file."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    self._sent_recipients = set(data.get('sent_recipients', []))
                logger.info("Loaded %d previously contacted recipients", len(self._sent_recipients))
            except Exception as e:
                logger.warning("Could not load DM tracking file: %s", e)
                self._sent_recipients = set()
        else:
            logger.info("No DM tracking file found, starting fresh")
    
    def _save(self) -> None:
        """Save sent recipients to file."""
        try:
            self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracking_file, 'w') as f:
                json.dump({
                    'sent_recipients': sorted(list(self._sent_recipients))
                }, f, indent=2)
        except Exception as e:
            logger.error("Could not save DM tracking file: %s", e)
    
    def has_been_contacted(self, recipient: str) -> bool:
        """Check if a recipient has already been contacted.
        
        Args:
            recipient: Username or user ID (with or without @ prefix)
        
        Returns:
            True if recipient was previously contacted
        """
        # Normalize recipient (remove @ if present, lowercase)
        normalized = recipient.lstrip('@').lower()
        return normalized in self._sent_recipients
    
    def mark_contacted(self, recipient: str) -> None:
        """Mark a recipient as contacted.
        
        Args:
            recipient: Username or user ID (with or without @ prefix)
        """
        # Normalize recipient (remove @ if present, lowercase)
        normalized = recipient.lstrip('@').lower()
        if normalized not in self._sent_recipients:
            self._sent_recipients.add(normalized)
            self._save()
            logger.info("Marked %s as contacted (%d total)", recipient, len(self._sent_recipients))
    
    def get_uncontacted_recipients(self, recipients: list[str]) -> list[str]:
        """Filter a list of recipients to only those not yet contacted.
        
        Args:
            recipients: List of usernames or user IDs
        
        Returns:
            Filtered list of recipients who haven't been contacted
        """
        uncontacted = []
        for recipient in recipients:
            if not self.has_been_contacted(recipient):
                uncontacted.append(recipient)
            else:
                logger.info("Skipping %s - already contacted", recipient)
        return uncontacted
    
    def reset(self) -> None:
        """Clear all tracking data. USE WITH CAUTION."""
        self._sent_recipients.clear()
        self._save()
        logger.warning("DM tracking data has been reset")
    
    def get_stats(self) -> dict:
        """Get statistics about contacted recipients."""
        return {
            'total_contacted': len(self._sent_recipients),
            'contacted_list': sorted(list(self._sent_recipients))
        }
