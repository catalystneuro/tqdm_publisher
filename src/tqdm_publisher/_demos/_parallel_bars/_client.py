"""Demo of parallel tqdm client."""

# HTTP server addition
import http.server
import json
import signal
import socket
import socketserver
import sys


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # Bind to a free port provided by the host
        return s.getsockname()[1]  # Return the port number assigned


def GLOBAL_CALLBACK(request_id, id, n, total, **kwargs):
    print("Global Update", request_id, id, f"{n}/{total}")


def create_http_server(port: int, callback):
    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

        def do_POST(self):
            content_length = int(self.headers["Content-Length"])
            post_data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            callback(post_data["request_id"], post_data["id"], **post_data["data"])
            self.send_response(200)
            self.end_headers()

    with socketserver.TCPServer(("", port), MyHttpRequestHandler) as httpd:

        def signal_handler(signal, frame):
            print("\n\nInterrupt signal received. Closing server...")
            httpd.server_close()
            httpd.socket.close()
            print("Server closed.")
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, signal_handler)
        except:
            pass # Allow to work in thread

        print(f"Serving HTTP on port {port}")
        httpd.serve_forever()


if __name__ == "__main__":

    flags_list = sys.argv[1:]

    port_flag = "--port" in flags_list

    if port_flag:
        port_index = flags_list.index("--port")
        PORT = int(flags_list[port_index + 1])
    else:
        PORT = find_free_port()

    create_http_server(port=PORT, callback=GLOBAL_CALLBACK)
