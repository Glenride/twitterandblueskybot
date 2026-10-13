# Quick Start Guide

## Start Both Bots (Most Common)
```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
./start_both_bots.sh
```

## Start Individual Bots
```bash
# Twitter only
./start_twitter_bot.sh

# Bluesky only
./start_bluesky_bot.sh
```

## Monitor Activity
```bash
# View Twitter logs
tail -f twitter.log

# View Bluesky logs
tail -f bluesky.log
```

## Stop Bots
- Press `Ctrl+C` in the terminal where bots are running
- Or: `pkill -f "twikit.bot"`

## Check What's Scheduled
```bash
source .venv/bin/activate
python -m twikit.bot.cli preview          # Twitter
python -m twikit.bot.bluesky_cli preview  # Bluesky
```

## Schedule Info
- Posts: **1.5-2 hours apart** (human-like timing)
- 30 posts over ~66 hours (~11 posts/day)
- Randomized intervals to avoid spam detection
- See [SCHEDULING_GUIDE.md](SCHEDULING_GUIDE.md) for details

## Reschedule Content
```bash
source .venv/bin/activate
python reschedule_posts.py
```

---

For detailed documentation, see [HOW_TO_START.md](HOW_TO_START.md)
