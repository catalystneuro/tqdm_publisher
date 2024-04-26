import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from tqdm_publisher._demos._multiple_bars._server import run_multiple_bar_demo
from tqdm_publisher._demos._parallel_bars._server import run_parallel_bar_demo
from tqdm_publisher._demos._single_bar._server import run_single_bar_demo

CLIENT_PORT = 1234

DEMOS = {
    "demo_single": dict(subpath="_single_bar", server=run_single_bar_demo),
    "demo_multiple": dict(subpath="_multiple_bars", server=run_multiple_bar_demo),
    "demo_parallel": dict(subpath="_parallel_bars", server=run_parallel_bar_demo),
}

DEMO_BASE_FOLDER_PATH = Path(__file__).parent

def _command_line_interface():
    """A simple command line interface for running the demo for TQDM Publisher."""
    if len(sys.argv) <= 1:
        print("No input provided. Please specify a command (e.g. 'demo').")
        return

    command = sys.argv[1]
    if "-" in command:
        print(
            f"No command provided, but flag {command} was received. "
            "Please specify a command before the flag (e.g. 'demo')."
        )
        return

    flags_list = sys.argv[2:]
    if len(flags_list) > 0:
        print(f"No flags are accepted at this time, but flags {flags_list} were received.")
        return

    if command in DEMOS:

        demo_info = DEMOS[command]

        client_relative_path = Path(demo_info["subpath"]) / "_client.html"
        subprocess.Popen(["python", "-m", "http.server", str(CLIENT_PORT), "-d", DEMO_BASE_FOLDER_PATH])

        webbrowser.open_new_tab(f"http://localhost:{CLIENT_PORT}/{client_relative_path}")

        demo_info["server"]()
    else:
        print(f"{command} is an invalid command.")
