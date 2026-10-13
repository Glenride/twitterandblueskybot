# Glenride Twitter & Bluesky Bot

Automated social media posting bot for Twitter and Bluesky using scheduled content.

## Features

- ✅ Scheduled posts for Twitter
- ✅ Scheduled posts for Bluesky
- ✅ Reply scheduling
- ✅ Direct message scheduling (Twitter)
- ✅ **DM duplicate prevention** - Never message the same person twice
- ✅ Content library management
- ✅ 2FA authentication support
- ✅ Automatic cookie management
- ✅ Dry-run mode for testing

## Quick Start

```bash
# Start both Twitter and Bluesky bots
./start_both_bots.sh

# Or start individually
./start_twitter_bot.sh
./start_bluesky_bot.sh
```

See **[QUICK_START.md](QUICK_START.md)** for common commands or **[HOW_TO_START.md](HOW_TO_START.md)** for detailed documentation.

## Project Structure

```
.
├── start_both_bots.sh        # Start both bots simultaneously
├── start_twitter_bot.sh      # Start Twitter bot only
├── start_bluesky_bot.sh      # Start Bluesky bot only
├── .env.local                # Environment configuration
├── twitter-cookies.json      # Twitter session cookies
├── twitter.log               # Twitter bot logs
├── bluesky.log              # Bluesky bot logs
└── twikit/
    ├── bot/
    │   ├── cli.py            # Twitter bot CLI
    │   ├── bluesky_cli.py    # Bluesky bot CLI
    │   ├── scheduler.py      # Content scheduling logic
    │   ├── config.py         # Configuration management
    │   ├── content-library.json  # Content definitions
    │   └── platforms/        # Platform-specific implementations
    └── twikit/               # Core twikit library
```

## Configuration

Edit `.env.local` to configure credentials and settings:

- Twitter credentials and 2FA
- Bluesky credentials
- Content library path
- Logging settings

## Content Management

Edit `twikit/bot/content-library.json` to manage your scheduled content:

```json
{
  "posts": [
    {
      "id": "post-001",
      "text": "Your post text here",
      "scheduled_window": {
        "earliest": "2025-11-08T14:00:00Z",
        "latest": "2025-11-08T14:15:00Z"
      }
    }
  ]
}
```

### Human-Like Scheduling

Posts are scheduled **1.5-2 hours apart** with randomized timing to:
- ✅ Comply with platform terms of service
- ✅ Avoid spam detection
- ✅ Simulate natural human posting patterns

See **[SCHEDULING_GUIDE.md](SCHEDULING_GUIDE.md)** for details on rate limits and rescheduling.

## DM Duplicate Prevention

The bot automatically tracks DM recipients to prevent duplicate messages:

```bash
# View who's been contacted
python manage_dm_tracking.py stats

# Check specific recipient
python manage_dm_tracking.py check @username

# Manually mark as contacted
python manage_dm_tracking.py add @username
```

See **[DM_TRACKING_GUIDE.md](DM_TRACKING_GUIDE.md)** for complete details.

## Monitoring

```bash
# View logs in real-time
tail -f twitter.log
tail -f bluesky.log

# Preview scheduled actions
python -m twikit.bot.cli preview
python -m twikit.bot.bluesky_cli preview
```

## Technology Stack

- **Python 3.11+** with virtual environment
- **Twikit** - Twitter API wrapper (no API key required)
- **atproto** - Bluesky AT Protocol client
- **httpx** - HTTP client with proxy support
- **pyotp** - 2FA/TOTP support

## Support

For issues, check the troubleshooting section in [HOW_TO_START.md](HOW_TO_START.md)
