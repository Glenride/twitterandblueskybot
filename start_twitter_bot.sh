#!/bin/bash

# Navigate to the bot directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Run the Twitter bot
echo "Starting Twitter bot..."
python -m twikit.bot.cli run 2>&1 | tee -a twitter.log

# Deactivate when done
deactivate
