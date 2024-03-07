#!/usr/bin/env python

import asyncio
import json
import random
import threading
from typing import List
from uuid import uuid4
import time

import websockets

from tqdm_publisher import TQDMPublisher


def generate_task_durations(n = 100) -> List[float]:
    return [random.uniform(0, 1.0) for _ in range(n)]

def start_progress_bar(id, callback):
    durations = generate_task_durations()
    progress_bar = TQDMPublisher(durations)
    progress_bar.subscribe(lambda info: callback(id, info))
    for duration in progress_bar:
        time.sleep(duration)

class WebSocketHandler:
    def __init__(self):
        self.clients = {}
        pass


    async def send(self, id, data):
        await self.clients[id].send(json.dumps(data))

    async def handler(self, websocket):
        identifier = str(uuid4())
        self.clients[identifier] = websocket  # Register client connection

        def on_progress(id, info):

            asyncio.run(self.send(identifier, dict(
                id=id,
                payload=info
            )))

        try:
            async for message in websocket:

                info = json.loads(message)

                if (info["command"] == "start"):
                    thread = threading.Thread(target=start_progress_bar, args=[info["id"], on_progress])
                    thread.start()

        finally:
            del self.clients[identifier] # This is called when the connection is closed


async def spawn_server():
    handler = WebSocketHandler().handler
    async with websockets.serve(handler, "", 8000):
        await asyncio.Future()

def main():
    asyncio.run(spawn_server())

if __name__ == "__main__":
    main()
