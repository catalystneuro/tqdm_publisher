#!/usr/bin/env python

import asyncio
import json
import random
import threading
from typing import List
from uuid import uuid4

import websockets

from tqdm_publisher import TQDMPublisher


async def sleep_func(sleep_duration: float = 1) -> float:
    await asyncio.sleep(delay=sleep_duration)


def create_tasks():
    n = 10**5
    sleep_durations = [random.uniform(0, 5.0) for _ in range(n)]
    tasks = []

    for sleep_duration in sleep_durations:
        task = asyncio.create_task(sleep_func(sleep_duration=sleep_duration))
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

    async def run(self):
        for f in self.progress_bar:
            await f

    def stop(self):
        self.started = False
        self.clear()
        self.thread.join()

    def _subscribe(self, callback):
        callback_id = self.progress_bar.subscribe(callback)
        self.callback_ids.append(callback_id)

    async def run(self):
        if hasattr(self, "progress_bar"):
            print("Progress bar already running")
            return

        self.tasks = create_tasks()
        self.progress_bar = TQDMPublisher(asyncio.as_completed(self.tasks), total=len(self.tasks))

        for callback in self.callbacks:
            self._subscribe(callback)

        for f in self.progress_bar:
            await f

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


progress_handler = ProgressHandler()


class WebSocketHandler:
    def __init__(self):
        self.clients = {}

        # Initialize with any state you need
        pass

    def handle_task_result(self, task):
        try:
            task.result()  # This will re-raise any exception that occurred in the task
        except websockets.exceptions.ConnectionClosedOK:
            print("WebSocket closed while sending message")
        except Exception as e:
            print(f"Error in task: {e}")

    async def handler(self, websocket):
        id = str(uuid4())
        self.clients[id] = websocket  # Register client connection

        progress_handler.start()  # Start if not started

        def on_progress(info):
            task = asyncio.create_task(websocket.send(json.dumps(info)))
            task.add_done_callback(self.handle_task_result)  # Handle task result or exception

        progress_handler.subscribe(on_progress)

        try:
            async for message in websocket:
                print("Message from client received:", message)

        finally:
            # This is called when the connection is closed
            del self.clients[id]
            if len(self.clients) == 0:
                progress_handler.stop()


async def spawn_server():
    handler = WebSocketHandler().handler
    async with websockets.serve(handler, "", 8000):
        await asyncio.Future()  # run forever


def main():
    asyncio.run(spawn_server())


if __name__ == "__main__":
    main()
