"""
Command line utility for spider, export etc.
"""

import argparse
import logging
import signal
import sys
import json

from google.cloud import datastore

def handle_sigint(signum, frame):
    """
    Handles SIGINT, which occurs on Ctrl-C
    """
    print("\nInterrupted by SIGINT\n")
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser()

    # global flags
    parser.add_argument('--credentials-path', dest='credentials_path',
                        help='Path to the service account credentials JSON file',
                        default='/secrets/service-account.json')
    
    parser.add_argument('--loglevel', help="error, warn, info, or debug (default: info)",
                        default='info')

    # subcommands
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')

    # spider subcommand
    spider_parser = subparsers.add_parser('spider', help='Take jobs off the queue and spider')
    spider_parser.add_argument('--kind', default='spider-results', help='Datastore entity kind to write (default: spider-results)')
    spider_parser.add_argument('--url', help='Spider a URL instead of using jobs from the queue. For testing/debugging only.')
    spider_parser.add_argument('--job', help='Job JSON object. To spider one URL, write the result back and exit.')
    
    # manager subcommand
    manager_parser = subparsers.add_parser('manager', help='Adds spider jobs to the queue. By default, all green-directory URLs are added.')
    manager_parser.add_argument('--url', help='Add a job to spider a specific URL')

    # export subcommand
    export_parser = subparsers.add_parser('export', help='Export JSON data')
    export_parser.add_argument('--kind', default='spider-results', help='Datastore entity kind to export (default: spider-results)')


    args = parser.parse_args()

    # set log level
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    loglevel = args.loglevel.lower()
    if loglevel == 'error':
        logging.basicConfig(level=logging.ERROR)
    elif loglevel == 'warn':
        logging.basicConfig(level=logging.WARN)
    elif loglevel == 'debug':
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("selenium").setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
        loglevel = 'info'

    logging.debug("Called command %s", args.command)

    datastore_client = datastore.Client.from_service_account_json(args.credentials_path)

    if args.command == 'manager':

        import manager
        manager.create_jobs(args.url)
    
    elif args.command == 'export':

        import export
        export.export_results(datastore_client, args.kind)

    else:
        from spider import spider
        if args.url:
            # spider one URL for diagnostic purposes
            spider.test_url(args.url)
        elif args.job:
            job = json.loads(args.job)
            spider.execute_single_job(datastore_client, job, args.kind)
        else:
            spider.work_of_queue(datastore_client, args.kind)
