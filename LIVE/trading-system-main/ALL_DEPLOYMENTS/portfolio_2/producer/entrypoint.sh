#!/bin/bash

# Turn on bash's job control
set -m

# Start the Sentiment Analysis in the background
echo "Starting Sentiment Producer..."
python sentiment.py &

# Start the Stock Data Producer in the background
echo "Starting Stock Data Producer..."
python main.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?