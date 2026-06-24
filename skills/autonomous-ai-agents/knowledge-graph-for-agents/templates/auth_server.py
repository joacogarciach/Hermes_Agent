#!/usr/bin/env python3
"""Bearer-token / Basic-auth server for Traefik ForwardAuth middleware.

Reads the expected Authorization header from mounted files so the token is
never passed through shell env vars (shell glob expansion mangles tokens
containing ***, ?, or other metacharacters).

Mount two files:
  /auth_bearer.txt  ->  "Bearer <token>"
  /auth_basic.txt   ->  "Basic <base64(username:password)>"

When the client sends either header exactly, the server returns HTTP 200 and
Traefik forwards the request. Otherwise it returns 401 with a Basic auth
challenge so browsers show a normal login dialog.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler

with open("/auth_bearer.txt") as f:
    BEARER = f.read().strip()

with open("/auth_basic.txt") as f:
    BASIC = f.read().strip()


class Handler(BaseHTTPRequestHandler):
    def _check(self):
        auth = self.headers.get("Authorization", "")
        return auth == BEARER or auth == BASIC

    def do_GET(self):
        if self._check():
            self.send_response(200)
            self.end_headers()
            return
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Memgraph"')
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"unauthorized\n")

    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET
    do_PATCH = do_GET
    do_HEAD = do_GET
    do_OPTIONS = do_GET


HTTPServer(("0.0.0.0", 9000), Handler).serve_forever()
