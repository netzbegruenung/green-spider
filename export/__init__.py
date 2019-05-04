"""
Exports data from the database to JSON files for use in a static webapp
"""

import datetime
import logging
import sys
import os
from hashlib import md5

import json
import requests


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)

def export_results(client, entity_kind):
    """
    Export of the main results data
    """
    out = []

    # Load data from database
    query = client.query(kind=entity_kind)
    for entity in query.fetch():
        logging.debug(entity.key.name)
        out.append({
            'input_url': entity.key.name,
            'resulting_urls': entity.get('checks').get('url_canonicalization'),
            'created': entity.get('created').isoformat(),
            'meta': entity.get('meta'),
            'checks': entity.get('checks'),
            'rating': entity.get('rating'),
            'score': entity.get('score'),
        })

    output_filename = "/json-export/spider_result.json"
    with open(output_filename, 'w', encoding="utf8") as jsonfile:
        json.dump(out, jsonfile, indent=2, sort_keys=True, ensure_ascii=False, cls=DateTimeEncoder)
