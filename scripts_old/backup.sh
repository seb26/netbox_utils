#!/bin/bash

# Sebastian Reategui - 10/06/2024
# Backup `netbox-docker` database and media
# 
# Usage:
# 	netbox_backup.sh netbox-docker-name
# 
# Result:
#   netbox_backup_20240610_104000.tar.gz
#   Contents:
#       netbox-docker-name.tar.gz           Docker working folder (ymls, etc)
#       > netbox-docker-name-postgres-1
#           > postgres_db.sql               PostgreSQL database
#       > netbox-docker-name-netbox-1
#           > media.tar.gz                  Images/media attachments

DATETIME=$(date "+%Y%m%d_%H%M%S")
DOCKER_NAME=$1
DB_USERNAME=netbox
DB_PASSWORD=netbox

if [ $# -eq 0 ]; then
    echo "Quitting: Must specify name of docker container as first argument"
    exit 1
fi

if [ -n "$(docker ps -f "name=$DOCKER_NAME" -f "status=running" -q )" ]; then
    echo "Container $DOCKER_NAME is running"
else
    echo "Quitting: Container $DOCKER_NAME is not running. Check the name or run it first"
    exit 1
fi

echo "Backing up database..."
mkdir -p /tmp/netbox_backup_$DATETIME/$DOCKER_NAME-postgres-1
docker exec -e PGPASSWORD=$DB_PASSWORD -it $DOCKER_NAME-postgres-1 pg_dump --username $DB_USERNAME --host localhost > /tmp/netbox_backup_$DATETIME/$DOCKER_NAME-postgres-1/postgres_db.sql
echo "Done."

echo "Backing up media directory..."
mkdir -p /tmp/netbox_backup_$DATETIME/$DOCKER_NAME-netbox-1/
docker exec -it $DOCKER_NAME-netbox-1 tar cz -f /tmp/media_$DATETIME.tar.gz /opt/netbox/netbox/media
docker cp $DOCKER_NAME-netbox-1:/tmp/media_$DATETIME.tar.gz /tmp/netbox_backup_$DATETIME/$DOCKER_NAME-netbox-1/media.tar.gz
echo "Done."

echo "Backing up docker folder..."
DOCKER_WORKING_FOLDER=$(docker inspect $DOCKER_NAME-netbox-1 | sed -rn "s/^.*com.docker.compose.project.working_dir\"\: \"(.*?)\",.*$/\1/p")
if [ -d $DOCKER_WORKING_FOLDER ]; then
    echo "Located docker working directory at: $DOCKER_WORKING_FOLDER"
    tar cz -f /tmp/netbox_backup_$DATETIME/$DOCKER_NAME.tar.gz $DOCKER_WORKING_FOLDER
else
    echo "❌ Could not locate docker working directory. It will not be included in backup"
fi

echo "Compressing..."
tar czf netbox_backup_$DATETIME.tar.gz -C /tmp/netbox_backup_$DATETIME .
echo "✅ Backup at: ./netbox_backup_$DATETIME.tar.gz"

echo "Clean up tmp files..."
rm -r /tmp/netbox_backup_$DATETIME
echo "DONE."