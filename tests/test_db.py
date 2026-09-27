import unittest

from taskboard.db import add_task, connect, get_task, list_tasks, progress, search_tasks, set_done


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")

    def test_sample_tasks_are_loaded(self):
        self.assertEqual(len(list_tasks(self.conn)), 10)

    def test_empty_board(self):
        self.assertEqual(list_tasks(connect(":memory:", seed=False)), [])

    def test_add_and_get(self):
        task = add_task(self.conn, "Water the plants", due="2026-10-02", tags="home")
        self.assertEqual(get_task(self.conn, task["id"])["title"], "Water the plants")

    def test_filter_by_tag(self):
        titles = [task["title"] for task in list_tasks(self.conn, tag="work")]
        self.assertEqual(titles, ["Write project proposal", "Review pull requests"])

    def test_search(self):
        titles = [task["title"] for task in search_tasks(self.conn, "groceries")]
        self.assertEqual(titles, ["Buy groceries"])

    def test_mark_done(self):
        set_done(self.conn, 1)
        self.assertEqual(get_task(self.conn, 1)["done"], 1)

    def test_progress_counts(self):
        stats = progress(self.conn)
        self.assertEqual((stats["done"], stats["total"]), (2, 10))
