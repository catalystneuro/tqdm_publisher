import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from tqdm_publisher._demo._single_bar._server import run_single_bar_demo
from tqdm_publisher._demo._multiple._server import run_multiple_bar_demo

CLIENT_PORT = 1234

DEMOS = {
    "single": dict(
        subpath="_single_bar",
        server=run_single_bar_demo
    ),
    "multiple": dict(
        subpath="_multiple",
        server=run_multiple_bar_demo
    )
    # "parallel": "_parallel",
}

DEMO_BASE_FOLDER_PATH = Path(__file__).parent

RELATIVE_DEMO_BASE_FOLDER_PATH = DEMO_BASE_FOLDER_PATH.relative_to(Path.cwd())


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

        # if command == "parallel":
        #     client_relative_path = Path(subpath) / "_client.py"
        #     subprocess.Popen(['python', str(DEMO_BASE_FOLDER_PATH / subpath / "_server.py")])
        #     subprocess.Popen(['python', str(DEMO_BASE_FOLDER_PATH / subpath / "_client.py")])

        # else:

        client_relative_path = Path(demo_info["subpath"]) / "_client.html"
        subprocess.Popen(["python", "-m", "http.server", str(CLIENT_PORT), "-d", DEMO_BASE_FOLDER_PATH])

        webbrowser.open_new_tab(f"http://localhost:{CLIENT_PORT}/{client_relative_path}")

        demo_info["server"]()

    else:
        print(f"{command} is an invalid command.")
