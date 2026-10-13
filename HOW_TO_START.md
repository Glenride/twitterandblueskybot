# How to Start the Social Media Bots

## Quick Start

### Run Both Bots Together (Recommended)

From your terminal, navigate to the bot directory and run:

```bash
./start_both_bots.sh
```

This will start both Twitter and Bluesky bots simultaneously, running in the background with logs written to `twitter.log` and `bluesky.log`.

### Run Individual Bots

**Twitter only:**
```bash
./start_twitter_bot.sh
```

**Bluesky only:**
```bash
./start_bluesky_bot.sh
```

**Legacy script (Twitter only):**
```bash
./start_bot.sh
```

## Manual Start

### Twitter Bot
```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
source .venv/bin/activate
python -m twikit.bot.cli run
```

### Bluesky Bot
```bash
cd /Users/dvaughnhouse/Sites/glenrideTwitterBot1
source .venv/bin/activate
python -m twikit.bot.bluesky_cli run
```

## Available Commands

Both bots support these commands:

- `run` - Continuously run the scheduler (default)
- `once` - Process all actions that are ready right now, then exit
- `preview` - Print pending actions without executing them

Example:
```bash
source .venv/bin/activate
python -m twikit.bot.cli once          # Twitter
python -m twikit.bot.bluesky_cli once  # Bluesky
```

## Monitoring

When running both bots, you can monitor their activity:

```bash
# Watch Twitter logs
tail -f twitter.log

# Watch Bluesky logs
tail -f bluesky.log

# Watch both at once (split screen)
tail -f twitter.log & tail -f bluesky.log
```

## Stopping the Bots

- If started with `start_both_bots.sh`: Press `Ctrl+C` to stop both
- If running manually: Press `Ctrl+C` in the terminal
- To kill background processes: `pkill -f "twikit.bot"`

## Environment Configuration

The bots read configuration from `.env.local` file which includes:

**Twitter credentials:**
- `TWITTER_USERNAME`
- `TWITTER_PASSWORD`
- `TWITTER_EMAIL`
- `TWITTER_TOTP_SECRET` (for 2FA)
- `TWITTER_COOKIES` (path to cookies file)

**Bluesky credentials:**
- `BLUESKY_USERNAME`
- `BLUESKY_PASSWORD`

**General settings:**
- `BOT_CONFIG` (path to content library)
- `BOT_LOG` (logging level)

## Troubleshooting

**Error: "ModuleNotFoundError"**
- Make sure you've activated the virtual environment: `source .venv/bin/activate`
- If dependencies are missing, install them: `pip install -r twikit/requirements.txt`

**Error: "TWITTER_USERNAME and TWITTER_PASSWORD environment variables are required"**
- Verify your `.env.local` file exists and contains the required credentials

**Error: "BLUESKY_USERNAME and BLUESKY_PASSWORD environment variables are required"**
- Verify your `.env.local` file exists and contains the Bluesky credentials

**Bots won't start:**
- Check if the virtual environment exists: `ls .venv`
- Make sure scripts are executable: `chmod +x start_*.sh`
- Check logs for detailed error messages: `cat twitter.log` or `cat bluesky.log`
