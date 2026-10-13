# Scheduling Guide

## Human-Like Posting Strategy

The bots are configured to post with **human-like timing** to:
- ✅ Comply with Twitter/Bluesky terms of service
- ✅ Avoid appearing automated or spammy
- ✅ Maximize engagement by varying posting patterns

## Current Schedule Settings

### Posts
- **Interval**: 1.5 to 2 hours between posts (90-120 minutes)
- **Variation**: Random minute offsets to avoid predictable patterns
- **Example timing**: 14:00, 16:09, 18:34, 20:45, etc.
- **Total posts**: 30 posts over ~66 hours (2.75 days)

### Replies
- **Interval**: Similar to posts (1.5-2 hours)
- **Start**: 45 minutes after first post
- **Window**: 30-minute window for each reply (more flexible than posts)
- **Total replies**: 15 replies

### Direct Messages (DMs)
- **Interval**: 3-4 hours between DMs (180-240 minutes)
- **Start**: 3 hours after first post
- **Reason**: DMs are more sensitive; longer intervals reduce risk
- **Total DMs**: 5 DMs

## Platform Rate Limits

### Twitter (X)
- Posts: No strict limit, but avoid more than 1 post per hour consistently
- Replies: Similar to posts
- DMs: ~500 per day, but recommended <50 for new accounts
- **Our schedule**: Well within limits at ~10-12 posts/day

### Bluesky
- Posts: No published rate limits, but recommend similar human-like patterns
- Replies: Same as posts
- **Our schedule**: Conservative and human-like

## Rescheduling Content

If you need to reschedule all content (e.g., starting fresh):

```bash
# Edit the start time in reschedule_posts.py
# Then run:
source .venv/bin/activate
python reschedule_posts.py
```

**Edit this line in the script:**
```python
start_time = datetime(2025, 11, 8, 14, 0, 0, tzinfo=timezone.utc)
```

Change the date/time to your desired starting point.

## Best Practices

### ✅ DO
- Keep intervals between 1.5-2 hours for posts
- Vary the exact minute of posting (not always :00 or :30)
- Space DMs further apart (3-4+ hours)
- Post during normal business hours when possible
- Monitor logs for any rate limit warnings

### ❌ DON'T
- Post more than once per hour consistently
- Use exact intervals (e.g., every 2 hours on the dot)
- Send many DMs in a short period
- Run multiple bot instances on the same account
- Ignore rate limit warnings in logs

## Monitoring Schedule Compliance

### Preview scheduled actions
```bash
source .venv/bin/activate
python -m twikit.bot.cli preview
python -m twikit.bot.bluesky_cli preview
```

### Check logs for rate limit issues
```bash
grep -i "rate" twitter.log
grep -i "limit" twitter.log
```

## Schedule Analysis

Current schedule analysis:
- **Average post interval**: 2.2 hours
- **Minimum interval**: 1.5 hours (90 min)
- **Maximum interval**: 2.9 hours (174 min)
- **Total campaign duration**: 66 hours (~2.75 days)

This creates a natural, human-like posting pattern that:
- Avoids detection as automated
- Stays well within platform limits
- Maximizes long-term account health
- Maintains consistent presence without spam

## Emergency: Stopping the Bot

If you notice rate limit warnings or issues:

```bash
# Stop both bots immediately
pkill -f "twikit.bot"

# Or press Ctrl+C in the terminal running the bots
```

Then review logs and adjust scheduling before restarting.
