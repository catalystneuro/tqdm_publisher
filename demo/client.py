import subprocess

from pathlib import Path

client_path = Path(__file__).parent / "client.html"

def main():
    subprocess.run(["open", client_path])

if __name__ == "__main__":
    main()