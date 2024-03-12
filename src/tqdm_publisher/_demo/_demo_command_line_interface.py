import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from ._parallel._server import run_demo as _parallel_server
from ._server import run_demo as _server

DEMO_BASE_FOLDER_PATH = Path(__file__).parent

CLIENT_FILE_PATH = DEMO_BASE_FOLDER_PATH / "_client.html"
SERVER_FILE_PATH = DEMO_BASE_FOLDER_PATH / "_server.py"

PARALLEL_SERVER_FILE_PATH = DEMO_BASE_FOLDER_PATH / "_parallel" / "_server.py"
PARALLEL_CLIENT_FILE_PATH = DEMO_BASE_FOLDER_PATH / "_parallel" / "_client.py"

PORT_FLAG = "--port"
HOST_FLAG = "--host"
SERVER_FLAG = "--server"
CLIENT_FLAG = "--client"

SUBPROCESSES = []


def close_process():
    for process in SUBPROCESSES:
        process.terminate()  # Send SIGTERM to subprocess
    # sys.exit()


def signal_handler(signal, frame):
    close_process()


signal.signal(signal.SIGINT, signal_handler)


def run_demo(demo, flags):

    if demo == "demo":

        print(flags)

        # For convenience - automatically pop-up a browser window on the locally hosted HTML page
        if flags["client"]:
            if sys.platform == "win32":
                os.system(f'start "" "{CLIENT_FILE_PATH}"')
            else:
                SUBPROCESSES.append(subprocess.Popen(["open", CLIENT_FILE_PATH]))

        _server()

    elif demo == "parallel-demo":
        if flags["client"]:
            client_args = ["python", PARALLEL_CLIENT_FILE_PATH]
            if flags["both"]:
                client_args += [PORT_FLAG, str(flags["port"]), HOST_FLAG, flags["host"]]
            SUBPROCESSES.append(subprocess.Popen(client_args))
            if flags["both"]:
                time.sleep(1)  # Ensure server starts before client connects

        if flags["server"]:
            if flags["both"]:
                _parallel_server(flags["host"], flags["port"])
            else:
                _parallel_server()

            close_process()

    else:
        print(f"{demo} is an invalid demo option.")


def get_flag(flags, flag, default=None):
    if flag in flags:
        flag_index = flags.index(flag)
        return flags[flag_index + 1]
    return default


def _command_line_interface():
    """A simple command line interface for running the demo for TQDM Publisher."""
    if len(sys.argv) <= 1:
        print("No input provided. Please specify a command (e.g. 'demo').")
        return

    command = sys.argv[1]
    if "--" in command:
        print(
            f"No command provided, but flag {command} was received. "
            "Please specify a command before the flag (e.g. 'demo')."
        )
        return

    flags_list = sys.argv[2:]
    if len(flags_list) > 0:
        print(f"No flags are accepted at this time, but flags {flags_list} were received.")
        return

    client_flag = "--client" in flags_list
    server_flag = "--server" in flags_list
    both_flags = "--server" in flags_list and "--client" in flags_list

    flags = dict(
        client=not server_flag or both_flags,
        server=not client_flag or both_flags,
        both=(client_flag and server_flag) or (not client_flag and not server_flag),
        host=get_flag(flags_list, HOST_FLAG, "localhost"),
        port=get_flag(flags_list, PORT_FLAG, 8000),
    )

    try:
        run_demo(command, flags)
    except KeyboardInterrupt as e:
        print("\n\nInterrupt signal received. Shutting down subprocesses...")
    finally:
        close_process()
