import asyncio
import json
import random
import threading
from uuid import uuid4

import websockets

from tqdm_publisher import TQDMPublisher


async def _async_sleep(sleep_duration: float) -> None:
    await asyncio.sleep(delay=sleep_duration)


def create_tasks() -> None:
    """
    Emulate the completion time of imaginary tasks.

    Each 'task' sleeps for a random duration (uniformly continuous from 0 to 5 seconds).
    With a default of 100 tasks, this is expected to take ~4 minutes to complete.
    """
    number_of_tasks = 100
    task_durations = [random.uniform(0, 5.0) for _ in range(number_of_tasks)]

    tasks = []
    for task_duration in task_durations:
        task = asyncio.create_task(_async_sleep(sleep_duration=task_duration))
        tasks.append(task)

    return tasks


class ProgressHandler:
    def __init__(self):
        self.started = False
        self.callbacks = []
        self.callback_ids = []

    def subscribe(self, callback):
        self.callbacks.append(callback)

        if hasattr(self, "progress_bar"):
            self._subscribe(callback)

    def unsubscribe(self, callback_id):
        self.progress_bar.unsubscribe(callback_id)

    def clear(self):
        self.callbacks = []
        self._clear()

    def _clear(self):
        for callback_id in self.callback_ids:
            self.unsubscribe(callback_id)

        self.callback_ids = []

    # async def run(self):
    #     for f in self.progress_bar:
    #         await f

    def stop(self):
        self.started = False
        self.clear()
        self.thread.join()

    def _subscribe(self, callback):
        callback_id = self.progress_bar.subscribe(callback)
        self.callback_ids.append(callback_id)

    async def run(self):
        if hasattr(self, "progress_bar"):
            print("Progress bar already running!")
            return

        self.tasks = create_tasks()
        self.progress_bar = TQDMPublisher(iterable=asyncio.as_completed(self.tasks), total=len(self.tasks))

        for callback in self.callbacks:
            self._subscribe(callback)

        # Iterate the asynchronous tasks to trigger them
        for task in self.progress_bar:
            await task

        self._clear()
        del self.progress_bar

    def thread_loop(self):
        while self.started:
            asyncio.run(self.run())

    def start(self):
        if self.started:
            return

        self.started = True

        self.thread = threading.Thread(target=self.thread_loop)  # Start infinite loop of progress bar thread
        self.thread.start()


class WebSocketHandler:
    def handle_task_result(self, task) -> None:
        try:
            task.result()  # This will re-raise any exception that occurred in the task
        except websockets.exceptions.ConnectionClosedOK:
            print("WebSocket closed while sending message!")
        except Exception as e:
            print(f"Error in task: {e}")

    async def handler(self, websocket) -> None:
        # Setup progress bar
        progress_bar = TQDMPublisher(iterable=asyncio.as_completed(self.tasks), total=len(self.tasks))

        def on_progress(info: dict):
            """
            This is the primary callback interfacing with TQDM.

            It can
            """
            task = asyncio.create_task(websocket.send(json.dumps(obj=info)))
            task.add_done_callback(self.handle_task_result)  # Handle task result or exception

        callback_id = progress_bar.subscribe(on_progress)

        # Iterate the asynchronous tasks to trigger them
        for task in self.progress_bar:
            await task

        async for message in websocket:
            print("Message from client received:", message)


async def _spawn_server() -> None:
    handler = WebSocketHandler().handler
    async with websockets.serve(handler, "", 8000):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(_spawn_server())
