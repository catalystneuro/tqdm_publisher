import subprocess
import sys
from pathlib import Path

demo_base_path = Path(__file__).parent / "demo"

client_path = demo_base_path / "client.html"
server_path = demo_base_path/ "server.py"

def main():

    if (len(sys.argv) <= 1):
        print("Please specify a command.")
        return
    
    command = sys.argv[1]

    flags_list = sys.argv[2:]

    client_flag = "--client" in flags_list
    server_flag = "--server" in flags_list
    both_flags = "--server" in flags_list and "--client" in flags_list

    flags = dict(
        client = not server_flag or both_flags,
        server = not client_flag or both_flags,
    
    )

    if (command == "demo"):
        if flags["client"]:
            subprocess.run(["open", client_path])
        
        if flags["server"]:
            subprocess.run(["python", server_path])

    else:
        print(f"{command} is an invalid command.")


if __name__ == "__main__":
    main()