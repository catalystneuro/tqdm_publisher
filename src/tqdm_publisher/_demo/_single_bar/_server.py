import asyncio
import json
import threading
import time

import websockets

import tqdm_publisher


def start_progress_bar(*, progress_callback: callable) -> None:
    """
    Emulate running the specified number of tasks by sleeping the specified amount of time on each iteration.

    Defaults are chosen for a deterministic and regular update period of one second for a total time of one minute.
    """
    all_task_durations_in_seconds = [1.0 for _ in range(10)]  # Ten seconds at one second per task
    progress_bar = tqdm_publisher.TQDMPublisher(iterable=all_task_durations_in_seconds)

    def run_function_on_progress_update(format_dict: dict) -> None:
        """
        This is the injected callback that will be run on each update of the TQDM object.

        Its first and only positional argument must be the `format_dict` of the TQDM instance. Additional customization
        on outside parameters must be achieved by defining those fields at an outer scope and defining this
        server-specific callback inside the local scope.

        In this demo, we will execute the `progress_callback` whose protocol is known only to the WebSocketHandler.

        This specifically requires the `id` of the progress bar and the `format_dict` of the TQDM instance.
        """
        progress_callback(id=progress_bar.id, format_dict=format_dict)

    progress_bar.subscribe(callback=run_function_on_progress_update)

    for task_duration in progress_bar:
        time.sleep(task_duration)


def send_message_to_client(*, websocket: websockets.WebSocketServerProtocol, message: dict) -> None:
    """
    Send a message to a specific client.

    This expects a WebSocket connection and a message (dict) to send.
    """

    asyncio.run(websocket.send(message=json.dumps(obj=message)))


async def handler(websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle messages from the client and manage the client connections."""

    # Wait for messages from the client
    async for message in websocket:
        message_from_client = json.loads(message)

        if message_from_client["command"] == "start":

            # Start the progress bar in a separate thread
            thread = threading.Thread(
                target=start_progress_bar,
                # On each update of the progress bar, send this update to the requesting client
                kwargs=dict(
                    progress_callback=lambda id, format_dict: send_message_to_client(
                        websocket, dict(id=id, format_dict=format_dict)
                    )
                ),
            )
            thread.start()


async def spawn_server() -> None:
    """Spawn the server asynchronously."""
    async with websockets.serve(ws_handler=handler, host="", port=8000):
        await asyncio.Future()


def run_single_bar_demo() -> None:
    """Trigger the execution of the asynchronous spawn."""
    asyncio.run(spawn_server())


