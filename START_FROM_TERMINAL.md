# How to Start the Bots from Your Terminal

## ✅ Bots Stopped - Ready for You to Start

Both bots have been stopped and are ready for you to control from your own terminal.

---

## Quick Start (Recommended)

Open your terminal and run:

```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
./start_both_bots.sh
```

That's it! Both Twitter and Bluesky bots will start running.

---

## What This Does

- Starts both bots in the background
- Logs output to `twitter.log` and `bluesky.log`
- Keeps running even if you close the terminal
- Can be stopped with `Ctrl+C` or by running: `pkill -f "twikit.bot"`

---

## Monitor the Bots

### Watch logs in real-time

**Option 1: Separate terminal windows**
```bash
# Terminal 1 - Twitter logs
tail -f twitter.log

# Terminal 2 - Bluesky logs
tail -f bluesky.log
```

**Option 2: Combined view**
```bash
tail -f twitter.log & tail -f bluesky.log
```

### Check if bots are running
```bash
ps aux | grep "twikit.bot" | grep -v grep
```

You should see two processes if both are running.

---

## Alternative: Start Individual Bots

If you only want to run one at a time:

### Twitter only
```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
./start_twitter_bot.sh
```

### Bluesky only
```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
./start_bluesky_bot.sh
```

---

## Stop the Bots

### Method 1: Keyboard shortcut
If the terminal is in the foreground, press:
```
Ctrl+C
```

### Method 2: Kill command
From any terminal:
```bash
pkill -f "twikit.bot"
```

### Method 3: Kill specific bot
```bash
# Stop Twitter bot only
pkill -f "twikit.bot.cli"

# Stop Bluesky bot only
pkill -f "twikit.bot.bluesky_cli"
```

---

## Check What's Scheduled

Before starting, you can preview what will be posted:

```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
source .venv/bin/activate
python -m twikit.bot.cli preview
python -m twikit.bot.bluesky_cli preview
deactivate
```

---

## Current Schedule

Your bots will post with human-like timing:
- **Start date**: Nov 8, 2025 at 9:00 AM EST
- **30 posts** over ~66 hours (2.75 days)
- **Posting rate**: ~11 posts/day
- **Interval**: 1.5-2 hours between posts (randomized)

---

## Troubleshooting

### "Permission denied" error
Make scripts executable:
```bash
chmod +x start_both_bots.sh start_twitter_bot.sh start_bluesky_bot.sh
```

### "ModuleNotFoundError"
The scripts handle the virtual environment automatically. If you see this error, try:
```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
source .venv/bin/activate
pip install -r twikit/requirements.txt
```

### Bots won't start
Check the logs for errors:
```bash
tail -50 twitter.log
tail -50 bluesky.log
```

### Already running error
Stop existing bots first:
```bash
pkill -f "twikit.bot"
```

---

## Summary Commands

```bash
# Navigate to project
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1

# Start both bots
./start_both_bots.sh

# Monitor logs
tail -f twitter.log
tail -f bluesky.log

# Check status
ps aux | grep "twikit.bot" | grep -v grep

# Stop bots
pkill -f "twikit.bot"
```

---

**You're all set! The bots are ready to run from your terminal.** 🚀
