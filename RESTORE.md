## Restore

1. do all steps necessary to get the docker running for first time

2. copy the db sql to tmp
```bash
docker cp /backup/path/pg_dump.sql netbox-hazen-postgres-1:/tmp
```

3. database operations

  - delete the existing database
```bash
docker exec -it netbox-hazen-postgres-1 bash
PGUSER=netbox PGPASSWORD=netbox dropdb netbox -f
```
  - create a new empty db

```bash
PGUSER=netbox PGPASSWORD=netbox createdb netbox
```

  - apply the db sql
```bash
PGUSER=netbox PGPASSWORD=netbox psql < /tmp/pg_dump.sql
```

4. run any DB migrations
```bash
docker compose exec netbox /opt/netbox/netbox/manage.py migrate
```

5. copy the media.tar.gz to tmp
```bash
docker cp /backup/path/media.tar.gz netbox-hazen-netbox-1:/tmp
```

6. bash into that container as root, cd /, extract
```bash
docker exec -it --user root netbox-hazen-netbox-1 bash
root@4718bcc9773a:/opt/netbox/netbox# cd /
root@4718bcc9773a:/# tar -xf /tmp/media.tar.gz
```
