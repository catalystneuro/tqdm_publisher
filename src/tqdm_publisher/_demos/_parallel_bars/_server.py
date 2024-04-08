"""Demo of parallel tqdm."""

import asyncio
import json
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Union

import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS, cross_origin

from tqdm_publisher import TQDMProgressHandler, TQDMProgressPublisher
from tqdm_publisher._demos._parallel_bars._client import (
    create_http_server,
    find_free_port,
)

N_JOBS = 3

# Each outer entry is a list of 'tasks' to perform on a particular worker
# For demonstration purposes, each in the list of tasks is the length of time in seconds
# that each iteration of the task takes to run and update the progress bar (emulated by sleeping)
BASE_SECONDS_PER_TASK = 0.5  # The base time for each task; actual time increases proportional to the index of the task
NUMBER_OF_TASKS_PER_JOB = 10
TASK_TIMES: List[List[float]] = [
    [BASE_SECONDS_PER_TASK * task_index] * NUMBER_OF_TASKS_PER_JOB
    for task_index in range(1, NUMBER_OF_TASKS_PER_JOB + 1)
]

WEBSOCKETS = {}

## NOTE: TQDMProgressHandler cannot be called from a process...so we just use a global reference exposed to each subprocess
progress_handler = TQDMProgressHandler()


def forward_updates_over_server_side_events(request_id: str, progress_bar_id: str, n: int, total: int, **kwargs):
    # TODO: shouldn't this line use `create_progress_subscriber`? Otherwise consider making `.accounce` non-private
    progress_handler._announce(
        dict(request_id=request_id, progress_bar_id=progress_bar_id, format_dict=dict(n=n, total=total), **kwargs)
    )


class ThreadedHTTPServer:
    def __init__(self, port: int, callback):
        self.port = port
        self.callback = callback

    def run(self):
        create_http_server(port=self.port, callback=self.callback)

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.start()


def forward_to_http_server(url: str, request_id: str, progress_bar_id: int, n: int, total: int, **kwargs):
    """
    This is the parallel callback definition.
    Its parameters are attributes of a tqdm instance and their values are what a typical default tqdm printout
    to console would contain (update step `n` out of `total` iterations).
    """
    json_data = json.dumps(obj=dict(request_id=request_id, id=str(progress_bar_id), data=dict(n=n, total=total)))

    requests.post(url=url, data=json_data, headers={"Content-Type": "application/json"})


def _run_sleep_tasks_in_subprocess(
    task_times: List[float],
    iteration_index: int,
    request_id: str,
    url: str,
):
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
    request_id : int
        Identifier of the request.
    url : str
        The localhost URL to sent progress updates to.
    """

    subprogress_bar_id = uuid.uuid4()

    sub_progress_bar = TQDMProgressPublisher(
        iterable=task_times,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({id})",
        leave=False,
    )

    sub_progress_bar.subscribe(
        lambda format_dict: forward_to_http_server(
            url=url, request_id=request_id, progress_bar_id=subprogress_bar_id, **format_dict
        )
    )

    for sleep_time in sub_progress_bar:
        time.sleep(sleep_time)


def run_parallel_processes(*, all_task_times: List[List[float]], request_id: str, url: str):

    futures = list()
    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:

        # # Assign the parallel jobs
        for iteration_index, task_times_per_job in enumerate(all_task_times):
            futures.append(
                executor.submit(
                    _run_sleep_tasks_in_subprocess,
                    task_times=task_times_per_job,
                    iteration_index=iteration_index,
                    request_id=request_id,
                    url=url,
                )
            )

        total_tasks_iterable = as_completed(futures)
        total_tasks_progress_bar = TQDMProgressPublisher(
            iterable=total_tasks_iterable, total=len(TASK_TIMES), desc="Total tasks completed"
        )

        # The 'total' progress bar bas an ID equivalent to the request ID
        total_tasks_progress_bar.subscribe(
            lambda format_dict: forward_to_http_server(
                url=url, request_id=request_id, progress_bar_id=request_id, **format_dict
            )
        )

        # Trigger the deployment of the parallel jobs
        for _ in total_tasks_progress_bar:
            pass


def format_sse(data: str, event: Union[str, None] = None) -> str:
    message = f"data: {json.dumps(data)}\n\n"
    if event is not None:
        message = f"event: {event}\n{message}"
    return message


def listen_to_events():
    messages = progress_handler.listen()  # returns a queue.Queue
    while True:
        msg = messages.get()  # blocks until a new message arrives
        yield format_sse(msg)


app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"
PORT = find_free_port()


@app.route("/start", methods=["POST"])
@cross_origin()
def start():
    data = json.loads(request.data) if request.data else {}
    request_id = data["request_id"]
    run_parallel_processes(all_task_times=TASK_TIMES, request_id=request_id, url=f"http://localhost:{PORT}")
    return jsonify({"status": "success"})


@app.route("/events", methods=["GET"])
@cross_origin()
def events():
    return Response(listen_to_events(), mimetype="text/event-stream")


class ThreadedFlaskServer:
    def __init__(self, port: int):
        self.port = port

    def run(self):
        app.run(host="localhost", port=self.port)

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.start()


async def start_server(port):

    flask_server = ThreadedFlaskServer(port=3768)
    flask_server.start()

    # # DEMO ONE: Direct updates from HTTP server
    # http_server = ThreadedHTTPServer(port=port, callback=forward_updates_over_sse)
    # http_server.start()
    # await asyncio.Future()

    # DEMO TWO: Queue
    def update_queue(request_id: str, progress_bar_id: str, n: int, total: int, **kwargs):
        forward_updates_over_server_side_events(
            request_id=request_id, progress_bar_id=progress_bar_id, n=n, total=total
        )

    http_server = ThreadedHTTPServer(port=PORT, callback=update_queue)
    http_server.start()

    await asyncio.Future()


def run_parallel_bar_demo() -> None:
    """Asynchronously start the servers."""
    asyncio.run(start_server(port=PORT))


def _run_parallel_bars_demo(port: str, host: str):
    URL = f"http://{HOST}:{PORT}"

    request_id = uuid.uuid4()
    run_parallel_processes(all_task_times=TASK_TIMES, request_id=request_id, url=URL)


if __name__ == "main":
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

    _run_parallel_bars_demo(port=PORT, host=HOST)
