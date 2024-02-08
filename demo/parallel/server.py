"""Demo of parallel tqdm."""

# HTTP server addition
import http.server
import json
import socket
import socketserver
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple

import requests

from tqdm_publisher import TQDMPublisher


def _run_sleep_in_subprocess(args: Tuple[int, int]):
    """The operation to run on each subprocess."""
    repeat = args[0]
    iteration_index = args[1]
    id = args[2]
    url = args[3]

    iterable = range(repeat)
    sub_progress_bar = TQDMPublisher(
        iterable=iterable,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({id})",
        leave=False,
    )

    if url:

        def to_main_process(n: int, total: int, **kwargs):

            json_data = json.dumps(dict(id=str(id), data=dict(n=n, total=total)))

            requests.post(url, data=json_data, headers={"Content-Type": "application/json"})

        sub_progress_bar.subscribe(to_main_process)

    for _ in sub_progress_bar:
        time.sleep(0.5)


if __name__ == "__main__":
    number_of_jobs = 3
    repeats = [4, 6, 8, 10, 4, 8, 20, 10, 5, 12, 5, 4, 5, 5, 5]

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

    # Start the parallel jobs
    with ProcessPoolExecutor(max_workers=number_of_jobs) as executor:

        job_map = executor.map(
            _run_sleep_in_subprocess,
            [(repeat, iteration_index, uuid.uuid4(), URL) for iteration_index, repeat in enumerate(repeats)],
        )

        [_ for _ in job_map]  # perform iteration to deploy jobs
