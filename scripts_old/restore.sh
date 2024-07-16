#!/bin/bash

# Sebastian Reategui - 10/06/2024
# Restore `netbox-docker` database and media

DOCKER_NAME=$1
DB_USERNAME=netbox
DB_PASSWORD=netbox

read -p "Path to Netbox postgresql database backup (.sql): " RESTORE_NETBOX_DB_PATH
if [ ! -f $RESTORE_NETBOX_DB_PATH ]; then
	echo "Invalid filepath"
	exit 1
fi

echo "The following command must be run prior."
echo "⚠️  It removes the existing Netbox database irreversibly. This is safe to do only if you have fresh installed Netbox."
echo ""
echo "    PGPASSWORD=$DB_PASSWORD docker exec -it $DOCKER_NAME-postgres-1 psql --username $DB_USERNAME -c 'drop database netbox'"
echo ""
echo "Now, do the following:"
echo "    1. Answer N at this prompt to quit, then..."
echo "    2. Explicitly run this command by copy pasting from above."
echo "    3. Re-run this script and answer Y at this prompt."
echo ""
set -- $(locale LC_MESSAGES)
yesexpr="$1"; noexpr="$2"; yesword="$3"; noword="$4"
while true; do
	read -p "I have now removed the existing database (${yesword} / ${noword}): " yn
    if [[ "$yn" =~ $yesexpr ]]; then break; fi
    if [[ "$yn" =~ $noexpr ]]; then exit; fi
    echo "Answer ${yesword} / ${noword}."
done

read -p "Path to Netbox media directory (/opt/netbox/netbox/media) (.tar.gz): " RESTORE_NETBOX_MEDIA_PATH
if [ ! -f $RESTORE_NETBOX_MEDIA_PATH ]; then
	echo "Invalid filepath"
	exit 1
fi

