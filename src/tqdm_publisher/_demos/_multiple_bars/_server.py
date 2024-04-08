import asyncio
import json
import threading
import time

import websockets

import tqdm_publisher


async def handler(websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle messages from the client and manage the client connections."""

    class WebSocketProgressBar:
        """
        This is similar to the `send_progress_update_to_client` function from the single bar demo server.

        The translation of this approach into a scoped class definition is merely to showcase an alternative approach
        of the execution.
        """

        def __init__(self, request_id: str):
            super().__init__()
            self.request_id = request_id

        def update(self, format_dict: dict) -> None:
            """
            This is the function that will run on every update of the TQDM object.

            It will forward the progress to the client.
            """
            asyncio.run(
                websocket.send(message=json.dumps(obj=dict(format_dict=format_dict, request_id=self.request_id)))
            )

        def run(self):
            """
            Emulate running the specified number of tasks by sleeping the specified amount of time on each iteration.

            Defaults are chosen for a deterministic and regular update period of one second for a total time of
            seconds per bar.

            This is similar to the `start_progress_bar` function from the single bar demo server. This is simply a
            showcase of an alternative approach to defining and scoping the execution.
            """
            all_task_durations_in_seconds = [1.0 for _ in range(10)]  # Ten seconds at one task per second
            self.progress_bar = tqdm_publisher.TQDMProgressPublisher(iterable=all_task_durations_in_seconds)
            self.progress_bar.subscribe(callback=self.update)

            for task_duration in self.progress_bar:
                time.sleep(task_duration)

        def start(self):
            thread = threading.Thread(target=self.run)
            thread.start()

    # Wait for messages from the client
    async for message in websocket:
        message_from_client = json.loads(message)

        if message_from_client["command"] == "start":
            web_socket_progress_bar = WebSocketProgressBar(request_id=message_from_client["request_id"])
            web_socket_progress_bar.start()


async def spawn_server() -> None:
    """Spawn the server asynchronously."""
    async with websockets.serve(ws_handler=handler, host="", port=3768):
        await asyncio.Future()


def run_multiple_bar_demo() -> None:
    """Trigger the execution of the asynchronous spawn."""
    asyncio.run(spawn_server())
