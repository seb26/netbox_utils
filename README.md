## `backup.py`

For use with [netbox-docker](https://github.com/netbox-community/netbox-docker) instances.

This script backs up:
* the postgres database
* the media root path
* the docker working directory; and
* an API status dump containing version info.

### Installation

Requires:
* Python 3 - tested on 3.12
* Pip

Install dependencies:
```bash
pip install python-on-wheels
```
### Usage

Run, with the name of your docker container instance.
```bash
python backup.py netbox-docker-name
```

Output is a compressed archive (`.tar.gz`) in the shell working directory.

### Example

```
➜ python backup.py netbox-docker        
backup.py: Start.
Init: Docker name: netbox-docker
Init: Backup datetime: 20240619_091909
Init: Checking for containers of netbox-docker...
Init: Found Docker containers for netbox-docker
Init: ✅ netbox-docker-netbox-1 running
Init: ✅ netbox-docker-postgres-1 running
Init: Docker image: netbox:latest
Init: Docker Netbox version: v3.7.0-2.8.0
Init: Docker working directory: [path to working directory]
Init: Temp directory: ./netbox_backup_20240619_091909/netbox-docker_netbox-latest_v3.7.0-2.8.0
Database backup: Check if postgres container is up...
Database backup: Getting dump...
Database backup: 866.61 KB
Database backup: ✅ Done.
Media directory: Path at /opt/netbox/netbox/media
Media directory: Size: 5179.61 KB
Media directory: Tarring...
tar: Removing leading `/' from member names
Media directory: Copying to local...
Media directory: Clearing temp file in container filesystem
Media directory: ✅ Done.
Docker working directory: Copying...
Docker working directory: ✅ Done.
Dump Netbox status info: Gathering from http://localhost:8080/api/status/ ...
Dump Netbox status info: Received.
Dump Netbox status info: Dumping to file...
Dump Netbox status info: ✅ Done.
Compress backup: Compressing...
Compress backup: Path: backup_netbox-docker_20240619_091909.tar.gz
Compress backup: Filesize: 7127.45 KB
Compress backup: Cleaning up temp folder.
Compressing backup: ✅ Done.
backup.py: All done.
```

Output
```
./backup_netbox-docker-name_20240619_091034.tar.gz
	> netbox-docker-name_netbox-latest_v3.7.0-2.8.0/
		> netbox-docker-name/
			... [contents of docker working directory]
		> netbox-docker-name-netbox-1/
			media_20240619_091034.tar.gz
		> netbox-docker-name-postgres-1/
			pg_dump.sql
		> netbox-docker-name_status.json
```


