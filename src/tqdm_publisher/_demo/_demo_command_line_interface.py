import os
import subprocess
import sys
from pathlib import Path

from ._server import run_demo

DEMO_BASE_FOLDER_PATH = Path(__file__).parent

CLIENT_FILE_PATH = DEMO_BASE_FOLDER_PATH / "_client.html"
SERVER_FILE_PATH = DEMO_BASE_FOLDER_PATH / "_server.py"


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

    if command == "demo":
        # For convenience - automatically pop-up a browser window on the locally hosted HTML page
        if sys.platform == "win32":
            os.system(f'start "" "{CLIENT_FILE_PATH}"')
        else:
            subprocess.run(["open", CLIENT_FILE_PATH])

        run_demo()

    else:
        print(f"{command} is an invalid command.")
