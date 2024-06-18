#!/bin/bash
DOCKER_NAME=$1

echo "Dumping netbox system status..."
get_status_dump () {
    docker inspect $DOCKER_NAME-netbox-1 | python3 backup-get_system_status.py
}
STATUS_DUMP=get_status_dump

if [ $STATUS_DUMP -eq 1 ]; then
    echo "Got Netbox system status from REST API. Dumping to file..."
    $STATUS_DUMP > $DOCKER_NAME_status.json
else
    echo "❌ Could not get Netbox system status from REST API."
fi