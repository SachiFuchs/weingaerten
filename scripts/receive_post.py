"""Tiny local bridge for browser scraping: GET /<name> serves scripts/<name>, POST /<name> writes it."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DIR = Path(__file__).parent


def target(path):
    name = Path(path.lstrip("/") or "hornbach_raw.json").name
    return DIR / name


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_GET(self):
        body = target(self.path).read_bytes()
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if len(body) > 2:
            target(self.path).write_bytes(body)
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(str(len(body)).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()


HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
