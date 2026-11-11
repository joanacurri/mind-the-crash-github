"""Serve the dashboard on localhost and open it in the browser. No Quarto needed.

    python serve.py          (Windows: py serve.py)

The pages load their data with fetch, which browsers block on file://, hence the server.
"""
import http.server
import sys
import threading
import webbrowser
from functools import partial
from pathlib import Path

PORT = int(next((a for a in sys.argv[1:] if a.isdigit()), 4321))
ROOT = Path(__file__).parent


class Handler(http.server.SimpleHTTPRequestHandler):
    # Fixed types: on Windows the registry can map .js to text/plain, and modules then fail.
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".json": "application/json", ".css": "text/css",
                      ".woff2": "font/woff2", ".woff": "font/woff", ".svg": "image/svg+xml"}

    def log_message(self, *args):
        pass


def main():
    url = f"http://localhost:{PORT}/take-a-call.html"
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT),
                                             partial(Handler, directory=str(ROOT)))
    if "--no-browser" not in sys.argv:
        threading.Timer(1, webbrowser.open, [url]).start()
    print(f"Dashboard at {url}\nClose this window (or Ctrl+C) to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


main()
