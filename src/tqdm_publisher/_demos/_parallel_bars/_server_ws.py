"""Demo of parallel tqdm."""

import asyncio
import json
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

import requests
import websockets

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


def forward_updates_over_websocket(request_id, id, format_dict):
    ws = WEBSOCKETS.get(request_id)

    if ws:

        asyncio.run(
            ws["ref"].send(
                message=json.dumps(
                    obj=dict(
                        format_dict=format_dict,
                        id=id,
                        request_id=request_id,
                    )
                )
            )
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


class ThreadedQueueTask:
    def run(self):

        progress_queue = progress_handler.listen()

        while True:
            msg = progress_queue.get()
            forward_updates_over_websocket(**msg)

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.start()


def forward_to_http_server(url: str, request_id: str, id: int, format_dict: dict):
    """
    This is the parallel callback definition.
    Its parameters are attributes of a tqdm instance and their values are what a typical default tqdm printout
    to console would contain (update step `n` out of `total` iterations).
    """
    json_data = json.dumps(obj=dict(request_id=request_id, id=str(id), data=format_dict))

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
    id : int
        Identifier of ??.
    url : str
        The localhost URL to sent progress updates to.
    """

    id = uuid.uuid4()

    sub_progress_bar = TQDMPublisher(
        iterable=task_times,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({id})",
        leave=False,
    )

    sub_progress_bar.subscribe(lambda format_dict: forward_to_http_server(url, request_id, id, format_dict))

    for sleep_time in sub_progress_bar:
        time.sleep(sleep_time)


def run_parallel_processes(request_id, url: str):

    futures = list()
    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:

        # # Assign the parallel jobs
        for iteration_index, task_times in enumerate(TASK_TIMES):
            futures.append(
                executor.submit(
                    _run_sleep_tasks_in_subprocess,
                    task_times=task_times,
                    iteration_index=iteration_index,
                    request_id=request_id,
                    url=url,
                )
            )

        total_tasks_iterable = as_completed(futures)
        total_tasks_progress_bar = TQDMPublisher(
            iterable=total_tasks_iterable, 
            total=len(TASK_TIMES), 
            desc=f"Total tasks completed for {request_id}"
        )

        total_tasks_progress_bar.subscribe(
            lambda format_dict: forward_to_http_server(
                url=url, request_id=request_id, id=request_id, format_dict=format_dict
            )
        )

        for _ in total_tasks_progress_bar:
            pass

WEBSOCKETS = {}


async def handler(url: str, websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle messages from the client and manage the client connections."""

    connection_id = uuid.uuid4()

    # Wait for messages from the client
    async for message in websocket:
        message_from_client = json.loads(message)

        if message_from_client["command"] == "start":
            request_id = message_from_client["request_id"]
            WEBSOCKETS[request_id] = dict(ref=websocket, id=connection_id)
            run_parallel_processes(request_id, url)


async def spawn_server() -> None:
    """Spawn the server asynchronously."""

    PORT = find_free_port()

    URL = f"http://localhost:{PORT}"

    async with websockets.serve(ws_handler=lambda websocket: handler(URL, websocket), host="", port=3768):

        def update_queue(request_id, id, format_dict):
            progress_handler._announce(dict(request_id=request_id, id=id, format_dict=format_dict))

        http_server = ThreadedHTTPServer(port=PORT, callback=update_queue)
        http_server.start()

        queue_task = ThreadedQueueTask()
        queue_task.start()
        await asyncio.Future()


def run_parallel_bar_demo() -> None:
    """Trigger the execution of the asynchronous spawn."""
    asyncio.run(spawn_server())


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
