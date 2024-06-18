# do all steps necessary to get the docker running for first time

# copy the db sql to tmp
docker cp /tmp/postgres_db.sql netbox-hazen-postgres-1:/tmp

# delete the existing database
docker exec -it netbox-hazen-postgres-1 bash
0ab933270a14:/# PGUSER=netbox PGPASSWORD=netbox dropdb netbox -f
# create a new empty db
0ab933270a14:/# PGUSER=netbox PGPASSWORD=netbox createdb netbox
exit
# apply the db sql
0ab933270a14:/# PGUSER=netbox PGPASSWORD=netbox psql < /tmp/postgres_db.sql

# run any DB migrations
docker compose exec netbox /opt/netbox/netbox/manage.py migrate

# copy the media.tar.gz to tmp
docker cp /tmp/netbox-docker-netbox-1/media.tar.gz netbox-hazen-netbox-1:/tmp

# bash into that container as root, cd /, extract
docker exec -it --user root netbox-hazen-netbox-1 bash
root@4718bcc9773a:/opt/netbox/netbox# cd /
root@4718bcc9773a:/# tar -xf /tmp/media.tar.gz
