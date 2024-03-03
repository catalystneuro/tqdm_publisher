"""Demo of parallel tqdm."""

import json
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from typing import List

import requests

from tqdm_publisher import TQDMPublisher


def to_main_process(id: int, url: str, n: int, total: int, **kwargs):
    """
    This is the parallel callback definition.

    Its parameters are attributes of a tqdm instance and their values are what a typical default tqdm printout
    to console would contain (update step `n` out of `total` iterations).
    """
    json_data = json.dumps(obj=dict(id=str(id), data=dict(n=n, total=total)))

    requests.post(url=url, data=json_data, headers={"Content-Type": "application/json"})


def _run_sleep_tasks_in_subprocess(task_times: List[float], iteration_index: int, id: int, url: str):
    """
    Run a 'task' that takes a certain amount of time to run on each worker.

    In this case that task is simply time.sleep.

    Parameters
    ----------
    sleep_time : float
        The amount of time this task emulates having taken to complete.
    iteration_index : int
        The index of this task in the list of all tasks from the buffer map.
        Each index would map to a different tqdm position.
    id : int
        Identifier of ??.
    url : str
        The localhost URL to sent progress updates to.
    """
    sub_progress_bar = TQDMPublisher(
        iterable=task_times,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({id})",
        leave=False,
    )

    if url:
        sub_progress_bar.subscribe(to_main_process)

    for sleep_time in sub_progress_bar:
        time.sleep(sleep_time)


if __name__ == "__main__":
    number_of_jobs = 3

    # Each outer entry is a list of 'tasks' to perform on a particular worker
    # For demonstration purposes, each in the list of tasks is the length of time in seconds
    # that each iteration of the task takes to run and update the progress bar (emulated by sleeping)
    all_task_times: List[List[float]] = [
        [4.2, 6.7, 8.5, 10.3, 4.2, 8.1],
        [20.5, 10.7, 5.3],
        [12.4, 5.2, 4.9, 5.1],
        [5.7, 5.8],
    ]

    flags_list = sys.argv[1:]

    port_flag = "--port" in flags_list
    host_flag = "--host" in flags_list

    if port_flag:
        port_index = flags_list.index("--port")
        PORT = flags_list[port_index + 1]

    if host_flag:
        host_index = flags_list.index("--host")
        HOST = flags_list[host_index + 1]
    else:
        HOST = "localhost"

    URL = f"http://{HOST}:{PORT}" if port_flag else None

    with ProcessPoolExecutor(max_workers=number_of_jobs) as executor:
        # Assign the parallel jobs
        job_map = executor.map(
            _run_sleep_tasks_in_subprocess,
            [
                (task_times, iteration_index, uuid.uuid4(), URL)
                for iteration_index, task_times in enumerate(all_task_times)
            ],
        )

        # Perform iteration to deploy jobs
        for _ in job_map:
            pass
