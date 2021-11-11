"""
The manager module allows to fill the RQ job queue.
"""

import logging
import math
import os
import random
import shutil
import time
import json
from datetime import datetime

from git import Repo
from rq import Queue
import redis
import yaml
from yaml import Loader
from hashlib import sha256

import config

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

def clone_data_directory():
    """
    Clones the source of website URLs, the green directory,
    into the local file system using git
    """
    if os.path.exists(config.GREEN_DIRECTORY_LOCAL_PATH):
        shutil.rmtree(config.GREEN_DIRECTORY_LOCAL_PATH)
    Repo.clone_from(config.GREEN_DIRECTORY_REPO, config.GREEN_DIRECTORY_LOCAL_PATH)


def directory_entries():
    """
    Iterator over all data files in the cloned green directory
    """
    path = os.path.join(config.GREEN_DIRECTORY_LOCAL_PATH, config.GREEN_DIRECTORY_DATA_PATH)
    for root, _, files in os.walk(path):
        for fname in files:

            filepath = os.path.join(root, fname)
            if not filepath.endswith(".yaml"):
                continue

            with open(filepath, 'r', encoding='utf8') as yamlfile:
                for doc in yaml.load_all(yamlfile, Loader=Loader):
                    yield doc


def chunks(the_list, size):
    """
    Yield successive n-sized chunks from list the_list
    where n = size.
    """
    for i in range(0, len(the_list), size):
        yield the_list[i:i + size]


def create_jobs(url=None):
    """
    Read all URLs from green directory and fill a job database
    with one job per URL.

    Alternatively, if the url argument is given, only the given URL
    will be added as a spider job.
    """

    logging.info('Waiting for redis at %s' % REDIS_URL)
    redis_success = False
    while not redis_success:
        try:
            redis_conn = redis.from_url(REDIS_URL)
            redis_success = True
        except Exception as ex:
            logging.error(ex)
            time.sleep(5)

    queue = Queue('low', connection=redis_conn)

    # refresh our local clone of the green directory
    logging.info("Refreshing green-directory clone")
    clone_data_directory()

    # build the list of website URLs to run checks for
    logging.info("Processing green-directory")
    input_entries = []

    count = 0

    random.seed()

    for entry in directory_entries():

        if 'type' not in entry:
            logging.error("Entry without type")
            continue
        if 'urls' not in entry:
            logging.debug("Entry %s does not have any URLs.", repr_entry(entry))
            continue

        website_url = None
        for index in range(len(entry['urls'])):
            try:
                if entry['urls'][index]['type'] == "WEBSITE":
                    website_url = entry['urls'][index]['url']
                    if website_url:
                        if url is not None and website_url != url:
                            continue
                        input_entries.append({
                            "url": website_url,
                            "type": entry.get("type"),
                            "level": entry.get("level"),
                            "state": entry.get("state"),
                            "district": entry.get("district"),
                            "city": entry.get("city"),
                        })
                        count += 1
            except NameError:
                logging.error("Error in %s: 'url' key missing (%s)",
                              repr_entry(entry), entry['urls'][index])

    # Ensure the passed URL argument is really there, even if not part
    # of the directory.
    if url and count == 0:
        logging.info("Adding job for URL %s which is not part of green-directory", url)
        input_entries.append({
            "url": url,
            "type": None,
            "level": None,
            "state": None,
            "district": None,
            "city": None,
        })

    count = 0
    errorcount = 0
    logging.info("Writing jobs")

    count = 0
    for entry in input_entries:
        try:
            _ = queue.enqueue('job.run',
                job_timeout='300s',
                at_front=random.choice([True, False]),
                # keywords args passes on the job function
                kwargs={
                    'job': entry,
                })

            # Print job for debugging purposes
            print(json.dumps(entry))

            #logging.debug("Added job with ID %s for URL %s" % (enqueued_job.id, entry['url']))
            count += 1
        except Exception as e:
            errorcount += 1
            logging.error("Error adding job for URL %s: %s" % (entry['url'], e))
        
        # Write kubernetes Job
        make_k8s_job(entry, count)

        count += 1

    logging.info("Writing jobs done, %s jobs added", count)
    logging.info("%d errors while writing jobs", errorcount)


def make_k8s_job(job_data, count):
    now = datetime.utcnow().strftime('%Y%m%d%H%M')
    urlhash = sha256(job_data['url'].encode('utf-8')).hexdigest()[0:12]
    job_name = f'gs-{now}-{urlhash}'
    filename = f'{job_name}.yaml'
    batch_folder = math.floor(count / config.K8S_JOB_BATCH_SIZE)
    output_dir = os.path.join(config.K8S_JOBS_PATH, str(batch_folder))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    job_json = json.dumps(job_data)
    job_flag = f'\'--job={job_json}\''

    with open(config.K8S_JOB_TEMPLATE, "r") as template_file:
        template = template_file.read()
    
    template = template.replace('JOB_NAME', job_name)
    template = template.replace('POD_NAME', job_name)
    template = template.replace('JOB_FLAG', job_flag)

    with open(output_path, "w") as output:
        output.write(template)


def repr_entry(entry):
    """
    Return string representation of a directory entry,
    for logging/debugging purposes
    """
    ret = entry['type']
    if 'level' in entry:
        ret += "/" + entry['level']
    if 'state' in entry:
        ret += "/" + entry['state']
    if 'district' in entry:
        ret += "/" + entry['district']
    return ret
