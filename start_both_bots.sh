#!/bin/bash

# Navigate to the bot directory
cd "$(dirname "$0")"

echo "Starting both Twitter and Bluesky bots..."
echo "Logs will be written to twitter.log and bluesky.log"
echo "Press Ctrl+C to stop both bots"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Stopping bots..."
    kill $TWITTER_PID $BLUESKY_PID 2>/dev/null
    wait $TWITTER_PID $BLUESKY_PID 2>/dev/null
    echo "Both bots stopped"
    exit 0
}

# Set trap to catch Ctrl+C
trap cleanup SIGINT SIGTERM

# Start Twitter bot in background
./start_twitter_bot.sh &
TWITTER_PID=$!
echo "Twitter bot started (PID: $TWITTER_PID)"

# Give it a moment to start
sleep 2

# Start Bluesky bot in background
./start_bluesky_bot.sh &
BLUESKY_PID=$!
echo "Bluesky bot started (PID: $BLUESKY_PID)"

echo ""
echo "Both bots are running!"
echo "Twitter bot PID: $TWITTER_PID"
echo "Bluesky bot PID: $BLUESKY_PID"
echo ""
echo "Monitor logs with:"
echo "  tail -f twitter.log"
echo "  tail -f bluesky.log"
echo ""

# Wait for both processes
wait $TWITTER_PID $BLUESKY_PID
