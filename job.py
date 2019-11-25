from pprint import pprint
import json
import os
import docker


DOCKER_IMAGE = 'quay.io/netzbegruenung/green-spider:dev'

CREDENTIALS_PATH = '/secrets/datastore-writer.json'

client = docker.from_env()

pwd = os.path.abspath(".")
secrets_path = pwd + "/secrets"
chromedir_path = pwd + "/volumes/chrome-userdir"

volumes = {}
volumes[secrets_path] = {'bind': '/secrets', 'mode': 'ro'}
volumes[chromedir_path] = {'bind': '/opt/chrome-userdir', 'mode': 'rw'}


def run(job):
    print("This is the job we got:")
    pprint(job)

    cmd_template = ("python cli.py --credentials-path={path} "
                    " --loglevel=debug "
                    " spider "
                    " --job='{job_json}'")
    
    cmd = cmd_template.format(path=CREDENTIALS_PATH,
                              job_json=json.dumps(job))
    
    output = client.containers.run(image=DOCKER_IMAGE,
                          command=cmd,
                          remove=True,
                          shm_size='2G',
                          detach=False,
                          tty=False,
                          volumes=volumes)

    return output
