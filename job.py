"""
Dieses Script wird vom RQ worker ausgeführt, um einen einzelnen Job aus der
Spider-Warteschlange abzuarbeiten.
"""

import json
import os
from datetime import datetime
import time
import logging

import docker
from google.cloud import datastore

# Maximum oper-job runtime in seconds. This can be increased for second, third attempt
# via the environment JOB_TIMEOUT variable.
TIMEOUT = int(os.environ.get("JOB_TIMEOUT", "50"))

DOCKER_IMAGE = 'ghcr.io/netzbegruenung/green-spider:latest'

CREDENTIALS_PATH = '/secrets/datastore-writer.json'

client = docker.from_env()
low_level_client = docker.APIClient(base_url='unix://var/run/docker.sock')

datastore_client = datastore.Client.from_service_account_json("." + CREDENTIALS_PATH)

pwd = os.path.abspath(".")
secrets_path = pwd + "/secrets"
chromedir_path = pwd + "/volumes/chrome-userdir"
screenshots_path = pwd + "/screenshots"

volumes = {}
volumes[secrets_path] = {'bind': '/secrets', 'mode': 'ro'}
volumes[chromedir_path] = {'bind': '/opt/chrome-userdir', 'mode': 'rw'}
volumes[screenshots_path] = {'bind': '/screenshots', 'mode': 'rw'}

logger = logging.getLogger('rq.worker')
logger.setLevel(logging.DEBUG)

def run(job):
    """
    Runs a spider container with the given job.

    Returns the container logs. If the execution takes longer than the
    duration defined by the JOB_TIMEOUT environment variable (in seconds),
    the container gets killed.
    """
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

    # Data about this spider run, to be written to datastore
    key = datastore_client.key('spider-runs')
    entity = datastore.Entity(key=key)
    results = {
        'datetime': datetime.utcnow(),
        'url': job['url'],
        'success': True,
        'error': '',
        'duration_seconds': 0,
        'cpu_usage_seconds': 0,
        'network_received_bytes': 0,
        'network_transmitted_bytes': 0,
        'memory_max_bytes': 0,
    }

    # wait for finish
    start = datetime.utcnow()
    while True:
        time.sleep(1)

        clist = client.containers.list(filters={'id': id})
        if len(clist) == 0:
            break

        for c in clist:

            # Collect stats
            try:
                stats = low_level_client.stats(id, stream=False)

                cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage'] / 1000000000.0
                if 'networks' in stats:
                    network_received_bytes = stats['networks']['eth0']['rx_bytes']
                    network_transmitted_bytes = stats['networks']['eth0']['tx_bytes']
                
                memory_max_bytes = 0
                if 'max_usage' in stats['memory_stats']:
                    memory_max_bytes = stats['memory_stats']['max_usage']
                    results['memory_max_bytes'] = memory_max_bytes

                #logger.debug("Stats: CPU time %d Sec, RX %d KB, Mem %d MB" % (cpu_usage, network_received_bytes/1000, memory_max_bytes/1000000))

                if cpu_usage > 0:
                    results['cpu_usage_seconds'] = round(cpu_usage)
                
                if network_received_bytes > 0:
                    results['network_received_bytes'] = network_received_bytes

                if network_transmitted_bytes > 0:
                    results['network_transmitted_bytes'] = network_transmitted_bytes
                

            except docker.errors.APIError as e:
                logger.error("Could not get stats: %s" % e)
            except json.decoder.JSONDecodeError:
                # This means we didn't get proper stats
                pass
            
            runtime = (datetime.utcnow() - start).seconds
            results['duration_seconds'] = round(runtime)

            #if c.status != "running":
            #    logger.info("Container %s status: %s" % (c.id, c.status))

            if c.status == "exited":
                logger.debug("Container %s is exited." % c.id)
                break

            if runtime > TIMEOUT:
                c.kill()
                results['success'] = False
                results['error'] = 'TIMEOUT'
                entity.update(results)
                datastore_client.put(entity)
                raise Exception("Execution took too long. Killed container after %s seconds." % TIMEOUT)

    entity.update(results)
    datastore_client.put(entity)
    return results
