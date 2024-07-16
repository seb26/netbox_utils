#old
# Sebastian Reategui - 09/06/2024
# Backup `netbox-docker` database and media
# Result is a .sql.gz (db) and a media zip
# 
# Usage
# 	netbox_backup.sh netbox-docker-name

DATETIME=$(date "+%y%m%d_%H%M%S")
DOCKER_NAME=$1
DB_USERNAME=seb
DB_PASSWORD=netbox

echo "Backing up database..."
if docker exec -it $
docker exec -it "$DOCKER_NAME"-postgres-1 psql --username $DB_USERNAME --password $DB_PASSWORD < "netbox_backup_postgres_db_$DATETIME.sql"
echo "Done."
echo "Backing up media directory..."
docker exec -it "$DOCKER_NAME"-netbox-1 tar -czf /opt/netbox/netbox/media > "netbox_backup_media_$DATETIME.tar.gz" 
echo "Done."