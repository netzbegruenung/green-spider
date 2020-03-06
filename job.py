"""
Dieses Script wird vom RQ Worker ausgeführt, um einen einzelnen Job aus der
Spider-Warteschlange abzuarbeiten.
"""

from pprint import pprint
import json
import os
from datetime import datetime
import time

import docker

# Maximum oper-job runtime in seconds. This can be increased for second, third attempt
# via the environment JOB_TIMEOUT variable.
TIMEOUT = int(os.environ.get("JOB_TIMEOUT", "50"))

DOCKER_IMAGE = 'quay.io/netzbegruenung/green-spider:latest'

CREDENTIALS_PATH = '/secrets/datastore-writer.json'

client = docker.from_env()

pwd = os.path.abspath(".")
secrets_path = pwd + "/secrets"
chromedir_path = pwd + "/volumes/chrome-userdir"

volumes = {}
volumes[secrets_path] = {'bind': '/secrets', 'mode': 'ro'}
volumes[chromedir_path] = {'bind': '/opt/chrome-userdir', 'mode': 'rw'}


def run(job):
    cmd_template = ("python cli.py --credentials-path={path} "
                    " --loglevel=debug "
                    " spider "
                    " --job='{job_json}'")
    
    cmd = cmd_template.format(path=CREDENTIALS_PATH,
                              job_json=json.dumps(job))
    
    container = client.containers.run(image=DOCKER_IMAGE,
                          command=cmd,
                          detach=True,
                          remove=True,
                          shm_size='2G',
                          stdout=True,
                          stderr=True,
                          tty=False,
                          volumes=volumes)

    id = container.id

    logs = ""

    # wait for finish
    start = datetime.utcnow()
    while True:
        time.sleep(5)

        clist = client.containers.list(filters={'id': id})
        if len(clist) == 0:
            break

        for c in clist:
            if c.status != "running":
                print("Container %s status: %s" % (c.id, c.status))

            if c.status == "exited":
                break

            runtime = (datetime.utcnow() - start).seconds
            if runtime > TIMEOUT:
                logs = container.logs()
                c.kill()
                raise Exception("Execution took too long. Killed container after %s seconds." % TIMEOUT)

    return logs
