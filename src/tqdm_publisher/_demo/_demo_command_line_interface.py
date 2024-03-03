"""Command line interface for running the TQDM Publisher demo."""

import os
import subprocess
import sys
from pathlib import Path

demo_base_path = Path(__file__).parent

client_path = demo_base_path / "client.html"
server_path = demo_base_path / "server.py"


def _demo_command_line_interface():
    """Should be called only through the package entrypoint."""
    if len(sys.argv) <= 1:
        print("No command provided. Please specify a command (e.g. 'demo').")
        return

    command = sys.argv[1]

    flags_list = sys.argv[2:]

    client_flag = "--client" in flags_list
    server_flag = "--server" in flags_list
    both_flags = "--server" in flags_list and "--client" in flags_list

    flags = dict(
        client=not server_flag or both_flags,
        server=not client_flag or both_flags,
    )

    if command == "demo":
        if flags["client"]:
            if "win" in sys.platform:
                # Windows has some trouble executing using the correct base entrypoint
                os.system(f'start "" "{client_path}"')
            else:
                subprocess.run(["open", client_path])

        if flags["server"]:
            subprocess.run(["python", server_path])

    else:
        print(f"{command} is an invalid command.")
