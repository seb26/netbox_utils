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