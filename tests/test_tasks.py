import tempfile
import unittest
from pathlib import Path

from tasks import MAX_TITLE_LENGTH, TaskStore


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "tasks.json"
        self.store = TaskStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_starts_empty(self):
        self.assertEqual(self.store.list_tasks(), [])

    def test_add_strips_title(self):
        task = self.store.add("  Write the demo  ")
        self.assertEqual(task.title, "Write the demo")
        self.assertFalse(task.done)

    def test_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            self.store.add("   ")

    def test_rejects_long_title(self):
        with self.assertRaises(ValueError):
            self.store.add("x" * (MAX_TITLE_LENGTH + 1))

    def test_toggle_marks_done_and_back(self):
        task = self.store.add("Ship it")
        self.assertTrue(self.store.toggle(task.id).done)
        self.assertFalse(self.store.toggle(task.id).done)

    def test_done_tasks_sort_after_open(self):
        first = self.store.add("First")
        self.store.add("Second")
        self.store.toggle(first.id)
        titles = [t.title for t in self.store.list_tasks()]
        self.assertEqual(titles[-1], "First")

    def test_delete_removes_task(self):
        task = self.store.add("Temporary")
        self.store.delete(task.id)
        self.assertEqual(self.store.list_tasks(), [])

    def test_unknown_id_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.store.toggle("deadbeef")
        with self.assertRaises(KeyError):
            self.store.delete("deadbeef")

    def test_persists_between_instances(self):
        self.store.add("Survives a restart")
        reloaded = TaskStore(self.path)
        self.assertEqual([t.title for t in reloaded.list_tasks()], ["Survives a restart"])


if __name__ == "__main__":
    unittest.main()
