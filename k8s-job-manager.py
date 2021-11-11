import config

import os
from datetime import datetime
import time
import random
from pathlib import Path

import kubernetes

PENDING_LIMIT = 2
RUNNING_LIMIT = 4

INTERVAL = 10 # Seconds

def main():

    # Get jobs
    jobs = list(Path("./k8s-jobs").rglob("*.yaml"))
    random.seed()
    random.shuffle(jobs)

    kubernetes.config.load_kube_config(context='giantswarm-5jka7')
    v1client = kubernetes.client.CoreV1Api()
    k8sclient = kubernetes.client.ApiClient()

    start = datetime.utcnow()
    jobs_queued = 0

    while len(jobs) > 0:
        # Check whether there are pods pending
        pending_pods = v1client.list_pod_for_all_namespaces(
            watch=False,
            field_selector='status.phase=Pending',
            label_selector='app=green-spider')
        pending = list(pending_pods.items)

        # Get running pods
        running_pods = v1client.list_pod_for_all_namespaces(
            watch=False,
            field_selector='status.phase=Running',
            label_selector='app=green-spider')
        running = list(running_pods.items)

        now = datetime.utcnow()
        duration = now - start
        
        # Add new job to the queue
        if len(pending) < PENDING_LIMIT and len(running) < RUNNING_LIMIT:
            to_be_queued = RUNNING_LIMIT - len(running)
            for _ in range(to_be_queued):
                job_path = jobs.pop(0)
                jobs_queued += 1

                duration_per_job = duration / jobs_queued
                jobs_remaining = len(jobs)

                print(f'{jobs_queued} jobs queued in {duration} - {jobs_remaining} jobs (estimated {duration_per_job * jobs_remaining}) remaining at {int(duration_per_job.total_seconds())} seconds per job on average')
                kubernetes.utils.create_from_yaml(k8sclient, job_path)
                os.remove(job_path)

        time.sleep(INTERVAL)
    
    print('No more jobs left. Done.')

if __name__ == '__main__':
    main()
