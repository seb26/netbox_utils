from datetime import datetime
from pathlib import Path
from python_on_whales import docker
import argparse
import json
import requests
import shutil
import subprocess
import sys
import traceback

def _shell(cmd):
    return subprocess.run(
        cmd,
        shell = True,
        stderr = subprocess.PIPE,
        stdout = subprocess.PIPE,
    )

def main():
    def backup_database():
        print('Database backup: Check if postgres container is up...')
        if not container_postgres.state.running is True:
            print(f'Database backup: ❌ {container_postgres.name} is not up, cannot dump database.')
            print(f'Database backup: {container_postgres.name} - state:\n{container_postgres.state}')
        # Create subfolder
        backup_target = backup_root.joinpath(f'{container_postgres.name}')
        backup_target.mkdir(parents=True, exist_ok=True)
        # Dump the db
        print('Database backup: Getting dump...')
        db_dump = _shell(
            f"""docker exec -e PGUSER={docker_db_user} -e PGPASSWORD={docker_db_pass} -it {container_postgres.name} pg_dump --host localhost""",
        )
        db_dump_display_bytes = f'{ (len(db_dump.stdout) / 1024):.2f}'
        print(f'Database backup: {db_dump_display_bytes} KB')
        if db_dump.returncode == 0:
            with open(backup_target.joinpath('pg_dump.sql'), 'wb') as f:
                f.write(db_dump.stdout)
        else:
            print('Database backup: ❌ Error while dumping database.')
            print(db_dump.stderr)
        print('Database backup: ✅ Done.')

    def backup_media():
        # Identify media local path from "MEDIA_ROOT=/path"
        docker_media_path = (
            next(
                filter(
                    lambda x: x.startswith('MEDIA_ROOT'),
                    container_netbox.config.env
                )
            )
            .split('=')[1]
        )
        if docker_media_path:
            print(f'Media directory: Path at {docker_media_path}')
            filesize = container_netbox.execute(
                # Get filesize
                [ 'du', 'media/', '-sb', ],
            )
            try:
                if filesize:
                    filesize_bytes = int(filesize.split('\t')[0])
                    print(f'Media directory: Size: {filesize_bytes / 1024:.2f} KB')
            except Exception as e:
                print(f'Media directory: ❌ Could not get filesize of media directory. Exception: {type(e)} - {e}')
        else:
            print(f'Media directory: ❌ Could not identify MEDIA_ROOT environment variable. Cannot back up media directory')
            return
        # Create subfolder
        backup_target = backup_root.joinpath(f'{docker_name}-netbox-1')
        backup_target.mkdir(parents=True, exist_ok=True)
        # Tar the media directory
        # Done by tarring to tmp and then copying to local fs
        # This is necessary because piping has not worked
        print(f'Media directory: Tarring...')
        container_netbox.execute(
            [ 'tar', 'cz', '-f', f'/tmp/media_{backup_datetime}.tar.gz', docker_media_path, ],
            interactive = True,
            tty = True,
        )
        print(f'Media directory: Copying to local...')
        # Copy it from local fs
        docker.container.copy(
            (
                container_netbox.name,
                f'/tmp/media_{backup_datetime}.tar.gz'
            ),
            str(backup_target),
        )
        # Cleanup
        print(f'Media directory: Clearing temp file in container filesystem')
        container_netbox.execute(
            [ 'rm', f'/tmp/media_{backup_datetime}.tar.gz', ],
            interactive = True,
            tty = True,
        )
        print('Media directory: ✅ Done.')

    def backup_docker_folder():
        # Locating the work directory
        if Path(docker_working_dirpath).is_dir():
            backup_target = backup_root.joinpath(f'{docker_name}')
            # Copy the working directory
            print('Docker working directory: Copying...')
            try:
                shutil.copytree(
                    docker_working_dirpath,
                    backup_target,
                )
                print('Docker working directory: ✅ Done.')
            except Exception as e:
                print(f'Docker working directory: ❌ Exception {type(e)} - {e} while copying {docker_working_dirpath}')
                # traceback.print_exc(file=sys.stderr)
        else:
            print(f'Docker working directory: ❌ This path does not exist or is not readable: {docker_working_dirpath}')
            return
        
    def dump_status():
        host_ip = None
        host_port = None
        if container_netbox.host_config.port_bindings:
            try:
                first = next(iter(container_netbox.host_config.port_bindings))
                host_ip = container_netbox.host_config.port_bindings[first][0].host_ip
                if host_ip == '':
                    host_ip = 'localhost'
                host_port = container_netbox.host_config.port_bindings[first][0].host_port
            except Exception as e:
                print(f'⚠️ Unable to get Netbox server information from host config port bindings. Trying defaults. Exception: {type(e)} - {e}')
                traceback.print_exc(file=sys.stderr)
        if not host_ip and not host_port:
            print(f'⚠️ Unable to get Netbox server information from host config port bindings. Trying defaults.')
            host_ip = 'localhost'
            host_port = '8080'
        url = f'http://{host_ip}:{host_port}/api/status/'
        print(f'Dump Netbox status info: Gathering from {url} ...')
        try:
            r = requests.get(url)
        except Exception as e:
            print(f'⚠️ Unable to get Netbox server information from URL: {url}. Exception: {type(e)} - {e}')
            # traceback.print_exc(file=sys.stderr)
        if r.ok:
            print(f'Dump Netbox status info: Received.')
            print(f'Dump Netbox status info: Dumping to file...')
            status_dump = r.json()
            # Indent it and dump to file
            status_dump_output = json.dumps(status_dump, indent=4)
            dump_target = backup_root.joinpath(f'{docker_name}_status.json')
            with open(dump_target, 'w', encoding='utf-8') as f:
                f.write(status_dump_output)
            print(f'Dump Netbox status info: ✅ Done.')
        else:
            print(r)
    
    def output_backup(backup_target_dir: str = None, backup_target_filename: str = None):
        print('Output backup: Compressing...')
        if backup_target_dir:
            backup_target_dir = Path(backup_target_dir)
        else:
            # Write to the shell cwd
            backup_target_dir = Path('.')
        if backup_target_filename:
            backup_filename = Path(backup_target_filename)
        else:
            backup_filename = Path(f'backup_{docker_name}_{backup_datetime}.tar.gz')
        backup_filepath = backup_target_dir.joinpath(backup_filename)
        _shell(f'tar czf {backup_filepath} -C {backup_root_parent} .')
        print(f'Output backup: Path: {backup_filepath}')
        filesize = backup_filepath.stat().st_size
        print(f'Output backup: Filesize: {filesize / 1024:.2f} KB')
        print(f'Output backup: Cleaning up temp folder.')
        try:
            shutil.rmtree(backup_root_parent)
        except PermissionError:
            _shell(
                f'rm -r {backup_root_parent}'
            )
        except Exception as e:
            print(f'Output backup: ❌ Cleaning up temp folder - Exception {type(e)} - {e}')
        print(f'Output backup: ✅ Done.')
    
    parser = argparse.ArgumentParser()
    parser.add_argument("docker_name", help="name of netbox-docker compose instance")
    parser.add_argument("-o", "--output-dir", help="output directory path for the backup file")
    parser.add_argument("-O", "--output-file", help="output directory filepath and filename for the backup file")
    parser.add_argument("--user", help="netbox-docker database username", default='netbox')
    parser.add_argument("--password", help="netbox-docker database password", default='netbox')
    args = parser.parse_args()

    docker_name = args.docker_name
    docker_db_user = args.user
    docker_db_pass = args.password

    # Timestamp for the backup
    backup_datetime = datetime.today().strftime('%Y%m%d_%H%M%S')
    print(f'Init: Docker name: {docker_name}')
    print(f'Init: Backup datetime: {backup_datetime}')
    print(f'Init: Checking for containers of {docker_name}...')
    processes = docker.container.list( # `docker ps`
        filters = { 'name': docker_name },
    )
    container_netbox = None
    container_postgres = None
    for proc in processes:
        if proc.name == docker_name + '-netbox-1':
            container_netbox = proc
        if proc.name == docker_name + '-postgres-1':
            container_postgres = proc
        if container_netbox and container_postgres:
            break
    if container_netbox and container_postgres:
        print(f'Init: Found Docker containers for {docker_name}')
        for container in [ container_netbox, container_postgres ]:
            if container.state.running:
                print(f'Init: ✅ {container.name} running')
            else:
                print(f'Init: ❌ {container.name} is not running...')
                print(f'Init: ❌ {container.name} - State: {container.state}')
    else:
        print(f'Init: ❌ Could not determine if the netbox-docker instance is present at all. Check the name ({docker_name}) and/or ensure it is running first.')
        raise SystemExit
    docker_image = container_netbox.config.image
    print(f'Init: Docker image: {docker_image}')
    docker_netbox_version = container_netbox.config.labels.get('netbox.original-tag')
    print(f'Init: Docker Netbox version: {docker_netbox_version}')
    docker_working_dirpath = container_netbox.config.labels.get('com.docker.compose.project.working_dir')
    print(f'Init: Docker working directory: {docker_working_dirpath}')
    # Account for the colon used in docker image names
    docker_image_safe = ( 
        docker_image
        .replace(':', '-')
        .replace('/', '-')
    )
    # Establish tmp directory
    backup_root_parent = Path(f'/tmp/netbox_backup_{backup_datetime}')
    backup_root = backup_root_parent.joinpath(f'{docker_name}_{docker_image_safe}_{docker_netbox_version}')
    try:
        backup_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f'Init: ❌ Fatal - Could not write to the temp directory at: {backup_root}')
        print(f'Init: ❌ Exception {type(e)} - {e}')
        raise SystemExit
    print(f'Init: Temp directory: {backup_root.resolve()}')
    
    backup_database()
    backup_media()
    backup_docker_folder()
    dump_status()
    output_backup(args.output_dir, args.output_file)

if __name__ == '__main__':
    print('backup.py: Start.')
    main()
    print('backup.py: All done.')