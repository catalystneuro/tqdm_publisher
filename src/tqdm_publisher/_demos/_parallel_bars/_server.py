"""Demo of parallel tqdm."""

import asyncio
import json
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS, cross_origin

from tqdm_publisher import TQDMProgressHandler, TQDMProgressPublisher

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

## TQDMProgressHandler cannot be called from a process...so we just use a global reference exposed to each subprocess
progress_handler = TQDMProgressHandler()


def forward_to_http_server(url: str, request_id: str, progress_bar_id: int, format_dict: dict):
    """
    This is the parallel callback definition.
    Its parameters are attributes of a tqdm instance and their values are what a typical default tqdm printout
    to console would contain (update step `n` out of `total` iterations).
    """
    json_data = json.dumps(obj=dict(request_id=request_id, id=str(progress_bar_id), data=format_dict))

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
        Identifier of the request, provided by the client.
    url : str
        The localhost URL to sent progress updates to.
    """

    subprogress_bar_id = uuid.uuid4()

    sub_progress_bar = TQDMProgressPublisher(
        iterable=task_times,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({subprogress_bar_id})",
        leave=False,
    )

    sub_progress_bar.subscribe(
        lambda format_dict: forward_to_http_server(
            url=url, request_id=request_id, progress_bar_id=subprogress_bar_id, format_dict=format_dict
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
            iterable=total_tasks_iterable, total=len(all_task_times), desc=f"Total tasks completed for {request_id}"
        )

        # The 'total' progress bar bas an ID equivalent to the request ID
        total_tasks_progress_bar.subscribe(
            lambda format_dict: forward_to_http_server(
                url=url, request_id=request_id, progress_bar_id=request_id, format_dict=format_dict
            )
        )

        # Trigger the deployment of the parallel jobs
        for _ in total_tasks_progress_bar:
            pass


def format_server_sent_events(*, message_data: str, event_type: str = "message") -> str:
    """
    Format an `event_type` type server-sent event with `data` in a way expected by the EventSource browser implementation.

    With reference to the following demonstration of frontend elements.

    ```javascript
    const server_sent_event = new EventSource("/api/v1/sse");

    /*
     * This will listen only for events
     * similar to the following:
     *
     * event: notice
     * data: useful data
     * id: someid
     */
    server_sent_event.addEventListener("notice", (event) => {
      console.log(event.data);
    });

    /*
     * Similarly, this will listen for events
     * with the field `event: update`
     */
    server_sent_event.addEventListener("update", (event) => {
      console.log(event.data);
    });

    /*
     * The event "message" is a special case, as it
     * will capture events without an event field
     * as well as events that have the specific type
     * `event: message` It will not trigger on any
     * other event type.
     */
    server_sent_event.addEventListener("message", (event) => {
      console.log(event.data);
    });
    ```

    Parameters
    ----------
    message_data : str
        The message data to be sent to the client.
    event_type : str, default="message"
        The type of event corresponding to the message data.

    Returns
    -------
    formatted_message : str
        The formatted message to be sent to the client.
    """

    # message = f"event: {event_type}\n" if event_type != "" else ""
    # message += f"data: {message_data}\n\n"
    # return message

    message = f"data: {message_data}\n\n"
    if event_type != "":
        message = f"event: {event_type}\n{message}"
    return message


def listen_to_events():
    messages = progress_handler.listen()  # returns a queue.Queue
    while True:
        message_data = messages.get()  # blocks until a new message arrives
        yield format_server_sent_events(message_data=json.dumps(message_data))


app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"
PORT = 3768


@app.route("/start", methods=["POST"])
@cross_origin()
def start():
    data = json.loads(request.data) if request.data else {}
    request_id = data["request_id"]
    url = f"http://localhost:{PORT}/update"
    app.logger.info(url)

    run_parallel_processes(all_task_times=TASK_TIMES, request_id=request_id, url=url)
    return jsonify({"status": "success"})


@app.route("/update", methods=["POST"])
@cross_origin()
def update():
    data = json.loads(request.data) if request.data else {}
    request_id = data["request_id"]
    progress_bar_id = data["id"]
    format_dict = data["data"]

    # Forward updates over Sever-Side Events
    progress_handler.announce(dict(request_id=request_id, progress_bar_id=progress_bar_id, format_dict=format_dict))

    return jsonify({"status": "success"})

@app.route("/events", methods=["GET"])
@cross_origin()
def events():
    return Response(listen_to_events(), mimetype="text/event-stream")


async def start_server(port):
    app.run(host="localhost", port=port)


def run_parallel_bar_demo() -> None:
    """Asynchronously start the server."""
    asyncio.run(start_server(port=PORT))


def _run_parallel_bars_demo(port: str, host: str):
    URL = f"http://{host}:{port}/update"
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
