"""Demo of parallel tqdm."""

import asyncio
import json
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from typing import List

import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS, cross_origin

from tqdm_publisher import TQDMProgressHandler, TQDMPublisher
from tqdm_publisher._demos._parallel_bars._client import (
    create_http_server,
    find_free_port,
)

N_JOBS = 3

# Each outer entry is a list of 'tasks' to perform on a particular worker
# For demonstration purposes, each in the list of tasks is the length of time in seconds
# that each iteration of the task takes to run and update the progress bar (emulated by sleeping)
TASK_TIMES: List[List[float]] = [
    [0.1 for _ in range(100)],
    [0.2 for _ in range(100)],
    [0.3 for _ in range(10)],
    [0.4 for _ in range(10)],
    [0.5 for _ in range(10)],
]

WEBSOCKETS = {}

## NOTE: TQDMProgressHandler cannot be called from a process...so we just use a queue directly
progress_handler = TQDMProgressHandler()


def forward_updates_over_sse(request_id, id, n, total, **kwargs):
    progress_handler._announce(dict(request_id=request_id, id=id, format_dict=dict(n=n, total=total)))


class ThreadedHTTPServer:
    def __init__(self, port: int, callback):
        self.port = port
        self.callback = callback

    def run(self):
        create_http_server(port=self.port, callback=self.callback)

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.start()


def forward_to_http_server(url: str, request_id: str, id: int, n: int, total: int, **kwargs):
    """
    This is the parallel callback definition.
    Its parameters are attributes of a tqdm instance and their values are what a typical default tqdm printout
    to console would contain (update step `n` out of `total` iterations).
    """
    json_data = json.dumps(obj=dict(request_id=request_id, id=str(id), data=dict(n=n, total=total)))

    requests.post(url=url, data=json_data, headers={"Content-Type": "application/json"})


def _run_sleep_tasks_in_subprocess(
    args,
    # task_times: List[float], iteration_index: int, id: int, url: str
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
    id : int
        Identifier of ??.
    url : str
        The localhost URL to sent progress updates to.
    """

    task_times, iteration_index, request_id, url = args

    id = uuid.uuid4()

    sub_progress_bar = TQDMPublisher(
        iterable=task_times,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({id})",
        leave=False,
    )

    sub_progress_bar.subscribe(lambda format_dict: forward_to_http_server(url, request_id, id, **format_dict))

    for sleep_time in sub_progress_bar:
        time.sleep(sleep_time)


def run_parallel_processes(request_id, url: str):

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:

        # Assign the parallel jobs
        job_map = executor.map(
            _run_sleep_tasks_in_subprocess,
            [(task_times, iteration_index, request_id, url) for iteration_index, task_times in enumerate(TASK_TIMES)],
        )

        # Send initialization for pool progress bar
        forward_to_http_server(url, request_id, id=request_id, n=0, total=len(TASK_TIMES))

        for _ in job_map:
            pass


def format_sse(data: str, event=None) -> str:
    msg = f"data: {json.dumps(data)}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg


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
    run_parallel_processes(request_id, f"http://localhost:{PORT}")
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
    def update_queue(request_id, id, n, total, **kwargs):
        forward_updates_over_sse(request_id, id, n, total)

    http_server = ThreadedHTTPServer(port=PORT, callback=update_queue)
    http_server.start()

    await asyncio.Future()


def run_parallel_bar_demo() -> None:
    """Asynchronously start the servers"""
    asyncio.run(start_server(PORT))


if __name__ == "__main__":

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

    if URL is None:
        raise ValueError("URL is not defined.")

    # Just run the parallel processes
    request_id = uuid.uuid4()
    run_parallel_processes(request_id, URL)
