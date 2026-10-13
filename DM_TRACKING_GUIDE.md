# DM Tracking Guide

## Overview

The bot automatically tracks which recipients have received DMs to **prevent duplicate messages**. This ensures you never accidentally spam someone with the same message.

## How It Works

### Automatic Tracking
- When a DM is successfully sent, the recipient is automatically recorded
- The bot checks this list before sending any DM
- If a recipient is already in the list, they are skipped
- Tracking data is saved to `dm_recipients_sent.json`

### Tracking File
The tracking file stores recipients in a normalized format:
- Usernames are converted to lowercase
- The @ symbol is stripped
- Example: `@EdgeAIStrategist` → `edgeaistrategist`

### Current DM Recipients

Your current DMs target these recipients:
- `dm-001` → @EdgeAIStrategist
- `dm-002` → @WarehouseOpsLead
- `dm-003` → @LogisticsFintech
- `dm-004` → @SupplyChainInvestor
- `dm-005` → @ResilienceFounder

Each person will **only receive one DM**, even if:
- You restart the bot multiple times
- The same person appears in multiple DM entries
- You reschedule the DMs

## Managing DM Tracking

### View Statistics
```bash
python manage_dm_tracking.py stats
```

Shows:
- Total number of recipients contacted
- Complete list of contacted recipients

### Check a Specific Recipient
```bash
python manage_dm_tracking.py check @EdgeAIStrategist
```

Returns whether that person has been contacted yet.

### Manually Add a Recipient
If you contacted someone outside the bot, mark them as contacted:
```bash
python manage_dm_tracking.py add @EdgeAIStrategist
```

This prevents the bot from sending them a duplicate message.

### Remove a Recipient (Allow Re-contacting)
To allow the bot to contact someone again:
```bash
python manage_dm_tracking.py remove @EdgeAIStrategist
```

⚠️ **Use carefully** - only remove if you genuinely want to contact them again.

### Reset All Tracking
**⚠️ DANGER ZONE ⚠️** - Clears all tracking data:
```bash
python manage_dm_tracking.py reset
```

This will allow the bot to re-send DMs to everyone. Only use if you're sure!

## Tracking File Location

**Default location:** `/Users/dvaughnhouse/Sites/glenrideTwitterBot1/dm_recipients_sent.json`

The file looks like this:
```json
{
  "sent_recipients": [
    "edgeaistrategist",
    "logisticsfintech",
    "warehouseOpslead"
  ]
}
```

## Bot Behavior

### First Run
- Tracking file doesn't exist
- Bot will send DMs to all scheduled recipients
- Recipients are recorded as contacted

### Subsequent Runs
- Bot loads existing tracking file
- Checks each recipient before sending
- Skips anyone already in the file
- Only new recipients receive DMs

### Example Logs

**When all recipients are new:**
```
INFO: Sending DM dm-001 to 1 uncontacted recipients (filtered 0 already contacted)
INFO: Marked @EdgeAIStrategist as contacted (1 total)
```

**When some recipients were already contacted:**
```
INFO: Skipping @EdgeAIStrategist - already contacted
INFO: Sending DM dm-001 to 0 uncontacted recipients (filtered 1 already contacted)
INFO: All recipients for DM dm-001 have already been contacted, skipping
```

## Safety Features

### Duplicate Prevention
✅ Same person in multiple DM entries → Sent only once
✅ Bot restarts → Recipients still tracked
✅ Reschedule DMs → Recipients still tracked

### Platform-Specific
- **Twitter**: DM tracking is active
- **Bluesky**: DMs not supported (no tracking needed)

## Best Practices

### Before Running
```bash
# Check who's been contacted
python manage_dm_tracking.py stats

# Check specific person
python manage_dm_tracking.py check @TargetPerson
```

### After Manual Outreach
If you manually DM someone outside the bot:
```bash
python manage_dm_tracking.py add @PersonYouContacted
```

### Backup Your Tracking File
```bash
cp dm_recipients_sent.json dm_recipients_sent_backup.json
```

### Review Before Rescheduling
If you're rescheduling DMs with new recipients, review the tracking:
```bash
python manage_dm_tracking.py stats
```

## Troubleshooting

### "All recipients already contacted" but you didn't send anything
Check the tracking file:
```bash
cat dm_recipients_sent.json
```

If it's wrong, reset or remove specific recipients.

### Tracking file not updating
- Check file permissions
- Check logs for errors: `grep -i "dm" twitter.log`
- Verify DMs are enabled: `TWITTER_ENABLE_DMS=true` in `.env.local`

### Want to re-send to everyone
```bash
python manage_dm_tracking.py reset
```

Then restart the bot.

## Integration with Content Library

Your DMs are defined in `content-library.json`:

```json
{
  "dms": [
    {
      "id": "dm-001",
      "text": "Your message...",
      "recipients": {
        "handles": ["@EdgeAIStrategist"],
        "user_ids": [],
        "dynamic_sources": []
      }
    }
  ]
}
```

The tracking works with:
- ✅ `handles` - Twitter handles
- ✅ `user_ids` - Twitter user IDs  
- ✅ `dynamic_sources` - Dynamic recipient lists (e.g., new followers)

## Privacy & Data

The tracking file contains:
- Twitter usernames (without @)
- No personal information
- No message content
- No timestamps

It's safe to:
- ✅ Backup and restore
- ✅ Version control (if you want)
- ✅ Share with team members
- ❌ Do NOT share publicly (reveals your outreach list)

---

**Your DMs are now protected from duplicate sends!** 🛡️
