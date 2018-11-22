"""
The jobs module allows to create jobs for the queue and take jobs off the queue
"""

from datetime import datetime
import logging
import os
import random
import shutil

from git import Repo
import tenacity
import yaml
from google.api_core.exceptions import Aborted
from google.cloud import datastore

import config


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

    # ensure the passed URL argument is really there, even if not part
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
            "index": int(random.uniform(1000000, 9999999)),
        })

    count = 0
    logging.info("Writing jobs")

    entities = []

    for entry in input_entries:
        key = datastore_client.key(config.JOB_DATASTORE_KIND, entry["url"])
        entity = datastore.Entity(key=key)
        entity.update({
            "created": datetime.utcnow(),
            "type": entry["type"],
            "level": entry["level"],
            "state": entry["state"],
            "district": entry["district"],
            "city": entry["city"],
            "index": int(random.uniform(1000000, 9999999)),
        })
        entities.append(entity)

    # commmit to DB
    for chunk in chunks(entities, 300):
        logging.debug("Writing jobs chunk of length %d", len(chunk))
        datastore_client.put_multi(chunk)
        count += len(chunk)

    logging.info("Writing jobs done, %s jobs added", count)


@tenacity.retry(wait=tenacity.wait_exponential(),
                retry=tenacity.retry_if_exception_type(Aborted))
def get_job_from_queue(datastore_client):
    """
    Returns a URL from the queue
    """
    out = None

    query = datastore_client.query(kind=config.JOB_DATASTORE_KIND,
                                   order=['index'])
    for entity in query.fetch(limit=1):
        logging.debug("Got job: %s", entity)
        out = dict(entity)
        out["url"] = entity.key.name
        datastore_client.delete(entity.key)

    return out

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
