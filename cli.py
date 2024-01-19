import subprocess
import sys
from pathlib import Path

demo_base_path = Path(__file__).parent / "demo"

client_path = demo_base_path / "client.html"
server_path = demo_base_path/ "server.py"

def main():
    flags = sys.argv[1:]

    client_flag = "--client" in flags
    server_flag = "--server" in flags
    both_flags = "--server" in flags and "--client" in flags

    commands = dict(
        client = not server_flag or both_flags,
        server = not client_flag or both_flags,
    
    )

    if commands["client"]:
        subprocess.run(["open", client_path])
    
    if commands["server"]:
        subprocess.run(["python", server_path])


if __name__ == "__main__":
    main()