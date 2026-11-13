import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from app import make_server
from tasks import TaskStore


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class AppTests(unittest.TestCase):
    def setUp(self):
        os.environ["TASKAPP_QUIET"] = "1"
        self.tmp = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.tmp.name) / "tasks.json")
        self.server = make_server(self.store, host="127.0.0.1", port=0)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.05), daemon=True).start()
        self.opener = urllib.request.build_opener(_NoRedirect)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, path, data=None, content_type=None):
        req = urllib.request.Request(self.base + path, data=data)
        if content_type:
            req.add_header("Content-Type", content_type)
        try:
            with self.opener.open(req) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode()

    def post_form(self, path, fields):
        return self.request(path, urllib.parse.urlencode(fields).encode(),
                            "application/x-www-form-urlencoded")

    def post_json(self, path, payload):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return self.request(path, raw, "application/json")

    def test_home_page_renders(self):
        status, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("Session 3 attendees", body)

    def test_health(self):
        status, body = self.request("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_add_task_via_form(self):
        status, _ = self.post_form("/tasks", {"title": "Buy oat milk"})
        self.assertEqual(status, 303)
        _, body = self.request("/")
        self.assertIn("Buy oat milk", body)

    def test_titles_are_html_escaped(self):
        self.post_form("/tasks", {"title": "<script>alert(1)</script>"})
        _, body = self.request("/")
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_empty_title_shows_error(self):
        status, body = self.post_form("/tasks", {"title": "  "})
        self.assertEqual(status, 400)
        self.assertIn("be empty", body)

    def test_api_create_and_list(self):
        status, body = self.post_json("/api/tasks", {"title": "From the API"})
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(body)["title"], "From the API")
        _, listing = self.request("/api/tasks")
        self.assertEqual([t["title"] for t in json.loads(listing)], ["From the API"])

    def test_api_rejects_bad_json(self):
        status, _ = self.post_json("/api/tasks", b"not json")
        self.assertEqual(status, 400)
        status, _ = self.post_json("/api/tasks", ["a", "list"])
        self.assertEqual(status, 400)

    def test_toggle_and_delete(self):
        task = self.store.add("Toggle me")
        status, _ = self.request(f"/tasks/{task.id}/toggle", b"")
        self.assertEqual(status, 303)
        self.assertTrue(self.store.list_tasks()[0].done)
        status, _ = self.request(f"/tasks/{task.id}/delete", b"")
        self.assertEqual(status, 303)
        self.assertEqual(self.store.list_tasks(), [])

    def test_unknown_task_is_404(self):
        status, _ = self.request("/tasks/deadbeef/toggle", b"")
        self.assertEqual(status, 404)

    def test_unknown_route_is_404(self):
        status, _ = self.request("/nope")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
