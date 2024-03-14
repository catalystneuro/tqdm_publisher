import asyncio
import json
import threading
import time

import websockets

import tqdm_publisher


async def handler(websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle messages from the client and manage the client connections."""

    class WebSocketProgressBar(threading.Thread):

        def __init__(self, request_id: str):
            super().__init__()
            self.request_id = request_id

        def update(self, format_dict) -> None:
            """
            This is the function that will run on every update of the TQDM object.

            It will forward the progress to the client.
            """
            asyncio.run(
                websocket.send(message=json.dumps(obj=dict(request_id=self.request_id, format_dict=format_dict)))
            )

        def run(self):
            """
            Emulate running the specified number of tasks by sleeping the specified amount of time on each iteration.

            Defaults are chosen for a deterministic and regular update period of one second for a total time of one minute.
            """
            all_task_durations_in_seconds = [1.0 for _ in range(10)]  # Ten seconds at one task per second
            progress_bar = self.progress_bar = tqdm_publisher.TQDMPublisher(iterable=all_task_durations_in_seconds)
            progress_bar.subscribe(callback=self.update)

            for task_duration in progress_bar:
                time.sleep(task_duration)

        # def start(self):
        #     thread = threading.Thread(target=self.run_progress_bar)
        #     thread.start()

    # Wait for messages from the client
    async for message in websocket:
        message_from_client = json.loads(message)

        if message_from_client["command"] == "start":
            progress_bar = WebSocketProgressBar(request_id=message_from_client["request_id"])
            progress_bar.start()


async def spawn_server() -> None:
    """Spawn the server asynchronously."""
    async with websockets.serve(ws_handler=handler, host="", port=8000):
        await asyncio.Future()


def run_multiple_bar_demo() -> None:
    """Trigger the execution of the asynchronous spawn."""
    asyncio.run(spawn_server())


if __name__ == "__main__":
    run_demo()
