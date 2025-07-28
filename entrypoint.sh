#!/bin/bash
set -e

# Create cron job to run the script daily at 11:12 UTC
echo "15 11 * * * cd /app && python /app/run.py >> /app/cron.log 2>&1" > /tmp/crontab
crontab /tmp/crontab
rm /tmp/crontab

# Start cron service
service cron start

echo "Cron job has been set up to run daily at 11:12 UTC"
echo "Container will now sleep indefinitely to keep cron running"
echo "Check /app/cron.log for script output"

# Keep the container running
tail -f /dev/null