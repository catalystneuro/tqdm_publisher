"""Demo of parallel tqdm."""

# HTTP server addition
import http.server
import json
import socket
import socketserver
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple

import requests

from tqdm_publisher import TQDMPublisher

id_ref = uuid.uuid4()


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # Bind to a free port provided by the host
        return s.getsockname()[1]  # Return the port number assigned


def _run_sleep_in_subprocess(args: Tuple[int, int]):
    """The operation to run on each subprocess."""
    repeat = args[0]
    iteration_index = args[1]
    id = args[2]
    PORT = args[3]

    iterable = range(repeat)
    sub_progress_bar = TQDMPublisher(
        iterable=iterable,
        position=iteration_index + 1,
        desc=f"Progress on iteration {iteration_index} ({id})",
        leave=False,
    )

    url = f"http://localhost:{PORT}"

    def to_main_process(n: int, total: int, **kwargs):
        
        json_data = json.dumps(dict(
            id=str(id),
            update=dict(
                n = n,
                total = total
            )
        ))

        requests.post(url, data=json_data, headers={"Content-Type": "application/json"})

    sub_progress_bar.subscribe(to_main_process)

    for _ in sub_progress_bar:
        time.sleep(0.5)


class ParallelProgressHandler:
    def __init__(self):
        self.callbacks = {}
        self.started = False

    def _run_callbacks(self, id, format_dict):
        for callback in self.callbacks.values():
            callback(id, format_dict)

    def run_server(self, port):

        def run_callbacks(id, format_dict):
            self._run_callbacks(id, format_dict)

        class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

            def do_POST(self):
                content_length = int(self.headers["Content-Length"])
                post_data = json.loads(self.rfile.read(content_length).decode("utf-8"))
                run_callbacks(post_data["id"], post_data["update"])
                self.send_response(200)
                self.end_headers()

        with socketserver.TCPServer(("", port), MyHttpRequestHandler) as httpd:
            print(f"Serving HTTP on port {port}")
            httpd.serve_forever()

    def run(self, number_of_jobs: int, repeats: List[int]):
        """The main (outer) iteration run on the central managing process."""

        if self.started:
            return

        self.started = True

        PORT = find_free_port()

        # Start the server in a new thread
        server_thread = threading.Thread(target=self.run_server, args=[PORT])
        server_thread.daemon = True
        server_thread.start()

        # Start the parallel jobs
        with ProcessPoolExecutor(max_workers=number_of_jobs) as executor:

            job_map = executor.map(
                _run_sleep_in_subprocess,
                [(repeat, iteration_index, uuid.uuid4(), PORT) for iteration_index, repeat in enumerate(repeats)],
            )

            [_ for _ in job_map]  # perform iteration to deploy jobs

        server_thread.join()

    def subscribe(self, callback):
        id = uuid.uuid4()
        self.callbacks[id] = callback
        return id


if __name__ == "__main__":
    number_of_jobs = 3
    repeats = [4, 6, 8, 10, 4, 8, 20, 10, 5, 12, 5, 4, 5, 5, 5]

    def send_to_website(id, format_dict):
        print("Send to website", id, format_dict)

    parallel_progress_handler = ParallelProgressHandler()

    parallel_progress_handler.subscribe(send_to_website)

    parallel_progress_handler.run(number_of_jobs=number_of_jobs, repeats=repeats)
