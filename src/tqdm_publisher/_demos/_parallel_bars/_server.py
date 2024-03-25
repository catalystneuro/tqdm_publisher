"""Demo of parallel tqdm."""

import json
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from typing import List

import requests

from tqdm_publisher import TQDMPublisher, TQDMProgressHandler

import asyncio
import json
import time
import websockets
import threading
from tqdm_publisher._demos._parallel_bars._client import create_http_server, find_free_port

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

def forward_updates_over_websocket(request_id, id, n, total, **kwargs):
    ws = WEBSOCKETS.get(request_id)

    if ws:
        asyncio.run(
            ws["ref"].send(
                message=json.dumps(
                    obj=dict(
                        format_dict=dict(n=n, total=total),
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

    ## NOTE: TQDMProgressHandler cannot be called directly from a process...
    # sub_progress_bar = progress_handler.create(
    #     iterable=task_times,
    #     position=iteration_index + 1,
    #     desc=f"Progress on iteration {iteration_index} ({id})",
    #     leave=False,
    #     additional_metadata=dict(request_id=request_id, id=id),
    # )

    for sleep_time in sub_progress_bar:
        time.sleep(sleep_time)


def run_parallel_processes(request_id, url: str):

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:

        # Assign the parallel jobs
        job_map = executor.map(
            _run_sleep_tasks_in_subprocess,
            [
                (task_times, iteration_index, request_id, url)
                for iteration_index, task_times in enumerate(TASK_TIMES)
            ],
        )

        # Perform iteration to deploy jobs
        for _ in job_map:
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

    async with websockets.serve(ws_handler=lambda websocket: handler(URL, websocket), host="", port=8000):


        # DEMO ONE: Direct updates from HTTP server
        http_server = ThreadedHTTPServer(port=PORT, callback=forward_updates_over_websocket)
        http_server.start()
        await asyncio.Future()

        # # DEMO TWO: Queue
        # def update_queue(request_id, id, n, total, **kwargs):
        #     progress_handler._announce(dict(request_id=request_id, id=id, n=n, total=total))
            
        # http_server = ThreadedHTTPServer(port=PORT, callback=update_queue)
        # http_server.start()
        
        # queue_task = ThreadedQueueTask()
        # queue_task.start()
        # await asyncio.Future()


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

