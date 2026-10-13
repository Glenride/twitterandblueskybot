#!/usr/bin/env python3
"""Utility script to view and manage DM tracking."""

import argparse
import json
import sys
from pathlib import Path


def load_tracking_file(filepath: Path) -> dict:
    """Load the tracking file."""
    if not filepath.exists():
        return {'sent_recipients': []}
    
    with open(filepath, 'r') as f:
        return json.load(f)


def save_tracking_file(filepath: Path, data: dict) -> None:
    """Save the tracking file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def view_stats(filepath: Path) -> None:
    """Display tracking statistics."""
    data = load_tracking_file(filepath)
    recipients = data.get('sent_recipients', [])
    
    print(f"DM Tracking Statistics")
    print(f"=" * 60)
    print(f"Total recipients contacted: {len(recipients)}")
    print(f"\nContacted recipients:")
    if recipients:
        for recipient in sorted(recipients):
            print(f"  - @{recipient}")
    else:
        print("  (none yet)")


def check_recipient(filepath: Path, recipient: str) -> None:
    """Check if a specific recipient has been contacted."""
    data = load_tracking_file(filepath)
    recipients = set(data.get('sent_recipients', []))
    normalized = recipient.lstrip('@').lower()
    
    if normalized in recipients:
        print(f"✅ @{recipient} has already been contacted")
    else:
        print(f"❌ @{recipient} has NOT been contacted yet")


def add_recipient(filepath: Path, recipient: str) -> None:
    """Manually add a recipient to the contacted list."""
    data = load_tracking_file(filepath)
    recipients = set(data.get('sent_recipients', []))
    normalized = recipient.lstrip('@').lower()
    
    if normalized in recipients:
        print(f"⚠️  @{recipient} is already marked as contacted")
    else:
        recipients.add(normalized)
        data['sent_recipients'] = sorted(list(recipients))
        save_tracking_file(filepath, data)
        print(f"✅ Added @{recipient} to contacted list")


def remove_recipient(filepath: Path, recipient: str) -> None:
    """Remove a recipient from the contacted list (allows re-sending)."""
    data = load_tracking_file(filepath)
    recipients = set(data.get('sent_recipients', []))
    normalized = recipient.lstrip('@').lower()
    
    if normalized not in recipients:
        print(f"⚠️  @{recipient} is not in the contacted list")
    else:
        recipients.remove(normalized)
        data['sent_recipients'] = sorted(list(recipients))
        save_tracking_file(filepath, data)
        print(f"✅ Removed @{recipient} from contacted list (can be contacted again)")


def reset_tracking(filepath: Path) -> None:
    """Reset all tracking data."""
    confirm = input("⚠️  This will clear ALL DM tracking data. Are you sure? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return
    
    data = {'sent_recipients': []}
    save_tracking_file(filepath, data)
    print("✅ DM tracking data has been reset")


def main():
    parser = argparse.ArgumentParser(description="Manage DM tracking for the bot")
    parser.add_argument(
        '--file',
        default='dm_recipients_sent.json',
        help='Path to tracking file (default: dm_recipients_sent.json)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # View stats
    subparsers.add_parser('stats', help='View tracking statistics')
    
    # Check recipient
    check_parser = subparsers.add_parser('check', help='Check if a recipient has been contacted')
    check_parser.add_argument('recipient', help='Username to check (e.g., @EdgeAIStrategist)')
    
    # Add recipient
    add_parser = subparsers.add_parser('add', help='Manually mark a recipient as contacted')
    add_parser.add_argument('recipient', help='Username to add (e.g., @EdgeAIStrategist)')
    
    # Remove recipient
    remove_parser = subparsers.add_parser('remove', help='Remove a recipient (allows re-contacting)')
    remove_parser.add_argument('recipient', help='Username to remove (e.g., @EdgeAIStrategist)')
    
    # Reset
    subparsers.add_parser('reset', help='Reset all tracking data (USE WITH CAUTION)')
    
    args = parser.parse_args()
    
    filepath = Path(args.file)
    
    if args.command == 'stats' or args.command is None:
        view_stats(filepath)
    elif args.command == 'check':
        check_recipient(filepath, args.recipient)
    elif args.command == 'add':
        add_recipient(filepath, args.recipient)
    elif args.command == 'remove':
        remove_recipient(filepath, args.recipient)
    elif args.command == 'reset':
        reset_tracking(filepath)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
