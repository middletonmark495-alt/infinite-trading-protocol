#!/usr/bin/env python3
"""
ITP Dashboard – local server.
Serves static files and proxies authenticated Coinbase Advanced Trade API calls.

Usage:
    cd <repo-root>
    source .env          # loads COINBASE_API_KEY, COINBASE_API_SECRET, etc.
    python3 src/web/server.py

Then open: http://localhost:8000
"""

import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PORT     = int(os.environ.get("DASHBOARD_PORT", 8000))
CB_BASE  = "https://api.coinbase.com"
WEB_DIR  = os.path.dirname(os.path.abspath(__file__))

MIME = {
    ".html": "text/html",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".json": "application/json",
    ".ico":  "image/x-icon",
    ".png":  "image/png",
    ".svg":  "image/svg+xml",
}


def _cb_headers(method: str, path: str, body: str = "") -> dict:
    key    = os.environ.get("COINBASE_API_KEY", "")
    secret = os.environ.get("COINBASE_API_SECRET", "")
    ts     = str(int(time.time()))
    sig    = hmac.new(
        secret.encode(),
        f"{ts}{method.upper()}{path}{body}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        "CB-ACCESS-KEY":       key,
        "CB-ACCESS-SIGN":      sig,
        "CB-ACCESS-TIMESTAMP": ts,
        "Content-Type":        "application/json",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  [{time.strftime('%H:%M:%S')}] {fmt % args}")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, code: int, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> str:
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n).decode() if n else ""

    def _proxy(self, method: str, cb_path: str, body: str = ""):
        headers = _cb_headers(method, cb_path, body)
        url = f"{CB_BASE}{cb_path}"
        req = Request(url, method=method, headers=headers)
        if body:
            req.data = body.encode()
        try:
            with urlopen(req, timeout=10) as r:
                self._send(r.status, r.read(), "application/json")
        except HTTPError as e:
            self._send(e.code, e.read(), "application/json")
        except URLError as e:
            self._send(502, {"error": str(e)})

    def _static(self, path: str):
        if path in ("/", ""):
            path = "/index.html"
        fpath = os.path.join(WEB_DIR, path.lstrip("/"))
        if not os.path.isfile(fpath):
            self._send(404, {"error": "not found"})
            return
        ext  = os.path.splitext(fpath)[1]
        mime = MIME.get(ext, "application/octet-stream")
        with open(fpath, "rb") as f:
            self._send(200, f.read(), mime)

    # ── HTTP verbs ─────────────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path)
        if p.path.startswith("/api/coinbase/"):
            cb = p.path[len("/api/coinbase"):] + (f"?{p.query}" if p.query else "")
            self._proxy("GET", cb)
        else:
            self._static(p.path)

    def do_POST(self):
        p    = urlparse(self.path)
        body = self._read_body()
        if p.path.startswith("/api/coinbase/"):
            cb = p.path[len("/api/coinbase"):]
            self._proxy("POST", cb, body)
        else:
            self._send(404, {"error": "not found"})

    def do_DELETE(self):
        p = urlparse(self.path)
        if p.path.startswith("/api/coinbase/"):
            cb = p.path[len("/api/coinbase"):]
            self._proxy("DELETE", cb)
        else:
            self._send(404, {"error": "not found"})


def main():
    print(f"""
╔══════════════════════════════════════════════════╗
║   ITP Dashboard                                  ║
║   http://localhost:{PORT}                          ║
╚══════════════════════════════════════════════════╝
  Coinbase key: {'SET' if os.environ.get('COINBASE_API_KEY') else 'NOT SET — trading will be read-only'}
  Press Ctrl+C to stop.
""")
    HTTPServer(("", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
