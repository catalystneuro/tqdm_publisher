import asyncio
import json
import threading
import time
from typing import Any, Dict, List
from uuid import uuid4

import websockets

from tqdm_publisher import TQDMPublisher


def start_progress_bar(*, client_id: str, progress_bar_id: str, client_callback: callable) -> None:
    """
    Emulate running the specified number of tasks by sleeping the specified amount of time on each iteration.

    Defaults are chosen for a deterministic and regular update period of one second for a total time of one minute.
    """
    all_task_durations_in_seconds = [1.0 for _ in range(60)]  # One minute at one second per update
    progress_bar = TQDMPublisher(iterable=all_task_durations_in_seconds)

    def run_function_on_progress_update(format_dict: dict) -> None:
        """
        This is the injected callback that will be run on each update of the TQDM object.

        Its first and only positional argument must be the `format_dict` of the TQDM instance. Additional customization
        on outside parameters must be achieved by defining those fields at an outer scope and defining this
        server-specific callback inside the local scope.

        In this demo, we will execute the `client_callback` whose protocol is known only to the WebSocketHandler.
        """
        client_callback(client_id=client_id, progress_bar_id=progress_bar_id, format_dict=format_dict)

    progress_bar.subscribe(callback=run_function_on_progress_update)

    for task_duration in progress_bar:
        time.sleep(task_duration)


class WebSocketHandler:
    """
    This is a class that handles the WebSocket connections and the communication protocol
    between the server and the client.

    While we could have implemented this as a function, a class is chosen here to maintain reference
    to the clients within a defined scope.
    """

    def __init__(self) -> None:
        """Initialize the mapping of client IDs to ."""
        self.clients: Dict[str, Any] = dict()

    def forward_progress_to_client(self, *, client_id: str, progress_bar_id: str, format_dict: dict) -> None:
        """This is the function that will run on every update of the TQDM object. It will forward the progress to the client."""
        asyncio.run(self.send(client_id=client_id, data=dict(progress_bar_id=progress_bar_id, format_dict=format_dict)))

    async def send(self, client_id: str, data: dict) -> None:
        """Send an arbitrary JSON object `data` to the client identifier by `client_id`."""
        await self.clients[client_id].send(json.dumps(obj=data))

    async def handler(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Register new WebSocket clients and handle their messages."""
        client_id = str(uuid4())

        # Register client connection
        self.clients[client_id] = websocket

        # Wait for messages from the client
        try:
            async for message in websocket:
                message_from_client = json.loads(message)

                if message_from_client["command"] == "start":
                    thread = threading.Thread(
                        target=start_progress_bar,
                        kwargs=dict(
                            client_id=client_id,
                            progress_bar_id=message_from_client["progress_bar_id"],
                            client_callback=self.forward_progress_to_client,
                        ),
                    )
                    thread.start()

        # Deregister the client when the connection is closed
        finally:
            if client_id in self.clients:
                del self.clients[client_id]


async def spawn_server() -> None:
    """Spawn the server asynchronously."""
    handler = WebSocketHandler().handler
    async with websockets.serve(handler, "", 8000):
        await asyncio.Future()


def run_demo() -> None:
    """Trigger the execution of the asynchronous spawn."""
    asyncio.run(spawn_server())
