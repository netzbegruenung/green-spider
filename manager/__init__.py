"""
The manager module allows to fill the job queue.
"""

from datetime import datetime
import logging
import os
import random
import shutil
import time

from git import Repo
from google.api_core.exceptions import Aborted
from google.cloud import datastore
from rq import Queue
import redis
import tenacity
import yaml

import config

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

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
                for doc in yaml.load_all(yamlfile):
                    yield doc


def chunks(the_list, size):
    """
    Yield successive n-sized chunks from list the_list
    where n = size.
    """
    for i in range(0, len(the_list), size):
        yield the_list[i:i + size]


def create_jobs(datastore_client, url=None):
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

    q = Queue('low', connection=redis_conn)

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

    for entry in input_entries:
        try:
            enqueued_job = q.enqueue('job.run',
                # job_timeout: maximum runtime of this job.
                job_timeout='300s',
                # keywords args passes on the job function
                kwargs={
                    'job': entry,
                })
            logging.debug("Added job with ID %s for URL %s" % (enqueued_job.id, entry['url']))
            count += 1
        except Exception as e:
            errorcount += 1
            logging.error("Error adding job for URL %s: %s" % (entry['url'], e))

    logging.info("Writing jobs done, %s jobs added", count)
    logging.info("%d errors while writing jobs", errorcount)


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
