#!/bin/bash

# Navigate to the bot directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Run the bot with the config from the .env.local file
python -m twikit.bot.cli run

# Deactivate when done (usually won't reach here unless bot stops)
deactivate
