import asyncio
import json
import threading
import time

import websockets

import tqdm_publisher


def start_progress_bar(*, progress_callback: callable) -> None:
    """
    Emulate running the specified number of tasks by sleeping the specified amount of time on each iteration.

    Defaults are chosen for a deterministic and regular update period of one second for a total time of 10 seconds.
    """
    all_task_durations_in_seconds = [1.0 for _ in range(10)]  # Ten seconds at one second per task
    progress_bar = tqdm_publisher.TQDMProgressPublisher(iterable=all_task_durations_in_seconds)

    def run_function_on_progress_update(format_dict: dict) -> None:
        """
        This is the injected callback that will be run on each update of the TQDM object.

        Its first and only positional argument must be the `format_dict` of the TQDM instance. Additional customization
        on outside parameters must be achieved by defining those fields at an outer scope and defining this
        server-specific callback inside the local scope.

        In this demo, we will execute the `progress_callback` whose protocol is known only to the WebSocketHandler.

        This specifically requires the `id` of the progress bar and the `format_dict` of the TQDM instance.
        """
        progress_callback(format_dict=format_dict, progress_bar_id=progress_bar.progress_bar_id)

    progress_bar.subscribe(callback=run_function_on_progress_update)

    for task_duration in progress_bar:
        time.sleep(task_duration)


async def handler(websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle messages from the client and manage the client connections."""

    def send_progress_update_to_client(*, format_dict: dict, progress_bar_id: str) -> None:
        """
        This is the callback that actually sends the updated `format_dict` to the front end webpage.

        It must be defined within the scope of the handler so that the `websocket` is inherited from the higher level.
        """
        message = json.dumps(obj=dict(format_dict=format_dict, progress_bar_id=progress_bar_id))
        asyncio.run(websocket.send(message=message))

    # Wait for messages from the client
    async for message in websocket:
        message_from_client = json.loads(message)

        if message_from_client["command"] == "start":
            # Start the progress bar in a separate thread
            thread = threading.Thread(
                target=start_progress_bar, kwargs=dict(progress_callback=send_progress_update_to_client)
            )
            thread.start()


async def spawn_server() -> None:
    """Spawn the server asynchronously."""
    async with websockets.serve(ws_handler=handler, host="", port=3768):
        await asyncio.Future()


def run_single_bar_demo() -> None:
    """Trigger the execution of the asynchronous spawn."""
    asyncio.run(spawn_server())
