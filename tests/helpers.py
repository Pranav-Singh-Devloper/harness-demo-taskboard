"""A tiny WSGI test client for the task board."""
import io
import json
from datetime import date
from urllib.parse import urlencode, urlsplit
from wsgiref.util import setup_testing_defaults

from taskboard.db import connect
from taskboard.web import TaskboardApp

# The tests pretend that today is Thursday 1 October 2026.
TODAY = date(2026, 10, 1)


class Result:
    def __init__(self, status, headers, body):
        self.status = status
        self.status_code = int(status.split()[0])
        self.headers = dict(headers)
        self.text = body.decode("utf-8")

    def json(self):
        return json.loads(self.text)


class Client:
    """Runs requests against a fresh in-memory board (seeded with data/seed.json unless seed=False)."""

    def __init__(self, seed=True, today=TODAY):
        self.conn = connect(":memory:", seed=seed)
        self.app = TaskboardApp(self.conn, today=lambda: today)

    def request(self, method, url, body=b"", content_type=""):
        parts = urlsplit(url)
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": parts.path,
            "QUERY_STRING": parts.query,
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        setup_testing_defaults(environ)
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        body_out = b"".join(self.app(environ, start_response))
        return Result(captured["status"], captured["headers"], body_out)

    def get(self, url):
        return self.request("GET", url)

    def post(self, url, data=None):
        body = urlencode(data or {}).encode("utf-8")
        return self.request("POST", url, body, "application/x-www-form-urlencoded")

    def post_json(self, url, payload):
        """POST JSON. Pass bytes or str to send a raw (possibly invalid) body."""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if not isinstance(payload, bytes):
            payload = json.dumps(payload).encode("utf-8")
        return self.request("POST", url, payload, "application/json")
