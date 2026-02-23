#!/usr/bin/env sh
set -eu

# Fallback values if not provided
CRON_SCHEDULE="${CRON_SCHEDULE:-0 */6 * * *}"
TZ_VALUE="${TZ:-UTC}"
SCRAPER_COMMAND="${SCRAPER_COMMAND:-echo 'No scraper command provided'}"

# Ensure directories exist
mkdir -p /var/log
mkdir -p /etc/cron.d
mkdir -p /data

# Write out the crontab file
cat > /etc/cron.d/scraper_cron <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=${TZ_VALUE}
${CRON_SCHEDULE} cd /app && ${SCRAPER_COMMAND} >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

# Ensure appropriate permissions on the crontab definition
chmod 0644 /etc/cron.d/scraper_cron

# Load the crontab file into cron
crontab /etc/cron.d/scraper_cron

printf '[scheduler] starting cron with schedule: %s\n' "$CRON_SCHEDULE"
printf '[scheduler] running command: %s\n' "$SCRAPER_COMMAND"

# Execute cron in the foreground
exec cron -f
