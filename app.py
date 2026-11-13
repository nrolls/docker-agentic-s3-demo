"""Task app: a small web app for the Docker Sandboxes demo.

Standard library only. Run it with:

    python3 app.py

then open http://localhost:8000
"""

from __future__ import annotations

import html
import json
import os
import platform
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs

from tasks import Task, TaskStore

TEMPLATE = Template(
    (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
)
TASK_ACTION = re.compile(r"^/tasks/([0-9a-f]{8})/(toggle|delete)$")
MAX_BODY_BYTES = 10_000


def render_task(task: Task) -> str:
    title = html.escape(task.title)
    state = "done" if task.done else "open"
    label = "Undo" if task.done else "Done"
    return (
        f'<li class="task {state}">'
        f'<span class="title">{title}</span>'
        f'<span class="actions">'
        f'<form method="post" action="/tasks/{task.id}/toggle"><button>{label}</button></form>'
        f'<form method="post" action="/tasks/{task.id}/delete">'
        f'<button class="ghost">Delete</button></form>'
        f"</span></li>"
    )


def render_page(store: TaskStore, error: str = "") -> str:
    tasks = store.list_tasks()
    items = "\n".join(render_task(t) for t in tasks)
    return TEMPLATE.substitute(
        tasks_html=items or '<li class="empty">No tasks yet. Add one above.</li>',
        open_count=sum(1 for t in tasks if not t.done),
        total_count=len(tasks),
        error_html=f'<p class="error">{html.escape(error)}</p>' if error else "",
        python_version=platform.python_version(),
        machine=html.escape(platform.machine()),
    )


class TaskHandler(BaseHTTPRequestHandler):
    store: TaskStore  # set by make_server()
    server_version = "TaskApp/1.0"

    # ---- helpers ----
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: object) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json")

    def _html(self, status: int, page: str) -> None:
        self._send(status, page.encode(), "text/html; charset=utf-8")

    def _redirect_home(self) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body too large.")
        return self.rfile.read(length)

    def log_message(self, fmt: str, *args: object) -> None:
        if not os.environ.get("TASKAPP_QUIET"):
            super().log_message(fmt, *args)

    # ---- routes ----
    def do_GET(self) -> None:
        if self.path == "/":
            self._html(HTTPStatus.OK, render_page(self.store))
        elif self.path == "/api/tasks":
            self._json(HTTPStatus.OK, [t.to_dict() for t in self.store.list_tasks()])
        elif self.path == "/healthz":
            self._json(HTTPStatus.OK, {"status": "ok"})
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            body = self._read_body()
        except ValueError as exc:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": str(exc)})
            return

        if self.path == "/tasks":
            title = parse_qs(body.decode()).get("title", [""])[0]
            try:
                self.store.add(title)
            except ValueError as exc:
                self._html(HTTPStatus.BAD_REQUEST, render_page(self.store, error=str(exc)))
                return
            self._redirect_home()
            return

        if self.path == "/api/tasks":
            try:
                data = json.loads(body or b"{}")
            except json.JSONDecodeError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Body must be JSON."})
                return
            if not isinstance(data, dict):
                self._json(HTTPStatus.BAD_REQUEST, {"error": 'Send an object like {"title": "..."}.'})
                return
            try:
                task = self.store.add(str(data.get("title", "")))
            except ValueError as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._json(HTTPStatus.CREATED, task.to_dict())
            return

        match = TASK_ACTION.match(self.path)
        if match:
            task_id, action = match.groups()
            try:
                if action == "toggle":
                    self.store.toggle(task_id)
                else:
                    self.store.delete(task_id)
            except KeyError:
                self._json(HTTPStatus.NOT_FOUND, {"error": "task not found"})
                return
            self._redirect_home()
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})


def make_server(
    store: TaskStore | None = None, host: str = "0.0.0.0", port: int = 8000
) -> ThreadingHTTPServer:
    handler = type("BoundTaskHandler", (TaskHandler,), {"store": store or TaskStore()})
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = make_server(host=host, port=port)
    print(f"Task app running on http://localhost:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
