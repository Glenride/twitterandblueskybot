#!/bin/bash

# Navigate to the bot directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Run the Bluesky bot
echo "Starting Bluesky bot..."
python -m twikit.bot.bluesky_cli run 2>&1 | tee -a bluesky.log

# Deactivate when done
deactivate
