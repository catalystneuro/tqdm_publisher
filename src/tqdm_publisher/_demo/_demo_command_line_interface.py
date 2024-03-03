"""Command line interface for running the TQDM Publisher demo."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

demo_base_path = Path(__file__).parent

client_path = demo_base_path / "client.html"
server_path = demo_base_path / "server.py"
parallel_server_path = demo_base_path / "parallel" / "server.py"
parallel_client_path = demo_base_path / "parallel" / "client.py"

# List to keep track of subprocesses
subprocesses = []


def _close_subprocesses():
    for process in subprocesses:
        process.terminate()  # Send SIGTERM to subprocess
    sys.exit(0)


def _signal_handler(signal, frame):
    print("Interrupt signal received. Shutting down subprocesses...")
    _close_subprocesses()


signal.signal(signal.SIGINT, _signal_handler)


def _command_line_interface():
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
        both=(client_flag and server_flag) or (not client_flag and not server_flag),
    )

    if command == "demo":
        if flags["client"]:
            if sys.platform == "win32":
                os.system(f'start "" "{client_path}"')
            else:
                subprocess.run(["open", client_path])

        if flags["server"]:
            subprocess.run(["python", server_path])

    elif command == "parallel-demo":
        HOST = "localhost"
        PORT = 8000

        if "--port" in flags_list:
            port_index = flags_list.index("--port")
            PORT = flags_list[port_index + 1]
        elif both_flags:
            print(f"Port not provided. Using default port ({PORT})")

        if "--host" in flags_list:
            host_index = flags_list.index("--host")
            HOST = flags_list[host_index + 1]
        elif both_flags:
            print(f"Host not provided. Using default host ({HOST})")

        if flags["client"]:
            client_args = ["python", parallel_client_path]
            if flags["both"]:
                client_args += ["--port", str(PORT), "--host", HOST]
            subprocess.run(client_args)
            if flags["both"]:
                time.sleep(1)  # Ensure server starts before client connects

        if flags["server"]:
            server_args = ["python", parallel_server_path]
            if flags["both"]:
                server_args += ["--port", str(PORT), "--host", HOST]
            subprocess.run(server_args)

    else:
        print(f"{command} is an invalid command.")


if __name__ == "__main__":
    try:
        _command_line_interface()
    except KeyboardInterrupt:
        print("\n\nInterrupt signal received. Shutting down subprocesses...")
    finally:
        _close_subprocesses()