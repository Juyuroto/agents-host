import base64
import csv
import hmac
import html
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

import compta
from config import COMPTA_WEB_PASSWORD, COMPTA_WEB_USER

PORT = 3000
CSV_NAME = re.compile(r"[\w.-]+\.csv")
PAGE_HEAD = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>Compta SafOps</title>
<style>
body{font-family:sans-serif;margin:16px}
table{border-collapse:collapse}
td,th{border:1px solid #ccc;padding:4px 8px;text-align:left;white-space:nowrap}
</style></head><body>"""
PAGE_TAIL = "</body></html>"


def _authorized(header: str | None) -> bool:
    if not header or not header.startswith("Basic "):
        return False
    try:
        user, _, password = base64.b64decode(header[6:]).decode("utf-8").partition(":")
    except ValueError:
        return False
    return (hmac.compare_digest(user.encode(), COMPTA_WEB_USER.encode())
            and hmac.compare_digest(password.encode(), COMPTA_WEB_PASSWORD.encode()))


def _index() -> str:
    items = "".join(
        f'<li><a href="/{html.escape(p.name)}">{html.escape(p.name)}</a></li>'
        for p in sorted(compta.ROOT.glob("*.csv"))
    )
    return f"<h1>Compta SafOps</h1><ul>{items}</ul>"


def _table(path) -> str:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    head, *body = rows
    thead = "<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in head) + "</tr>"
    tbody = "".join(
        "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in body
    )
    return f'<p><a href="/">Retour</a></p><h1>{html.escape(path.name)}</h1><table>{thead}{tbody}</table>'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not _authorized(self.headers.get("Authorization")):
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="compta"')
            self.end_headers()
            return
        name = unquote(self.path.lstrip("/"))
        if name == "":
            return self._send(_index())
        path = compta.ROOT / name
        if not CSV_NAME.fullmatch(name) or not path.is_file():
            self.send_response(404)
            self.end_headers()
            return
        self._send(_table(path))

    def _send(self, body: str) -> None:
        data = (PAGE_HEAD + body + PAGE_TAIL).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve() -> None:
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
