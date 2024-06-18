#!/bin/bash
DOCKER_NAME=$1

echo "Dumping netbox system status..."
STATUS_DUMP=$(docker inspect $DOCKER_NAME-netbox-1 | python3 <(cat <<END
from pprint import pprint
import json, requests, sys, traceback
try:
    if sys.stdin:
        try:
            inspect = json.load(sys.stdin)[0]
        except:
            exit(1)
    else:
        exit(1)
except Exception as e:
    traceback.print_exc(file=sys.stderr)
    exit(1)
port_bindings = inspect.get('HostConfig').get('PortBindings')
if port_bindings:
    host_ip = None
    host_port = None
    try:
        host = port_bindings[next(iter(port_bindings))][0]
        host_ip = host.get('HostIp')
        host_port = host.get('HostPort')
    except IndexError:
        pass
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        exit(1)
    if not host_ip:
        host_ip = 'localhost'
    if not host_port:
        host_port = '8080'
try:
    url = f'http://{host_ip}:{host_port}/api/status/'
    r = requests.get(url)
    if r.ok:
        pprint(r.json())
        exit(0)
    else:
        exit(1)
except:
    exit(1)
END
) )
if [ !-z $STATUS_DUMP ]; then
    echo "Got Netbox system status from REST API. Dumping to file..."
    $STATUS_DUMP > $DOCKER_NAME_status.json
else
    echo "❌ Could not get Netbox system status from REST API."
fi