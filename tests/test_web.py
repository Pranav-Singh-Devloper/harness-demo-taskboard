import unittest

from tests.helpers import Client


class PagesTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Taskboard", response.text)
        self.assertIn("Write project proposal", response.text)

    def test_progress_line(self):
        self.assertIn("2 of 10 done", self.client.get("/").text)

    def test_task_page_renders_markdown(self):
        response = self.client.get("/tasks/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<strong>proposal</strong>", response.text)

    def test_unknown_task_is_404(self):
        self.assertEqual(self.client.get("/tasks/999").status_code, 404)

    def test_unknown_page_is_404(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)

    def test_search(self):
        self.assertIn("Buy groceries", self.client.get("/search?q=groceries").text)

    def test_tag_filter(self):
        text = self.client.get("/?tag=work").text
        self.assertIn("Review pull requests", text)
        self.assertNotIn("Buy groceries", text)

    def test_export_csv(self):
        response = self.client.get("/export.csv")
        self.assertTrue(response.headers["Content-Type"].startswith("text/csv"))
        self.assertEqual(response.text.splitlines()[0], "id,title,due,priority,tags,done")

    def test_stylesheet(self):
        self.assertEqual(self.client.get("/static/style.css").status_code, 200)


class FormActionsTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_task(self):
        response = self.client.post("/tasks", {"title": "Water the plants", "priority": "low", "tags": "home"})
        self.assertEqual(response.status_code, 303)
        self.assertIn("Water the plants", self.client.get("/").text)

    def test_create_task_needs_a_title(self):
        self.assertEqual(self.client.post("/tasks", {"title": "  "}).status_code, 400)

    def test_complete_task(self):
        self.client.post("/tasks/1/done")
        self.assertTrue(self.client.get("/api/tasks/1").json()["done"])

    def test_delete_task(self):
        response = self.client.post("/tasks/1/delete")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.client.get("/tasks/1").status_code, 404)


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_list(self):
        tasks = self.client.get("/api/tasks").json()
        self.assertEqual(len(tasks), 10)
        self.assertEqual(tasks[1]["tags"], ["home", "errands"])

    def test_get_unknown_task(self):
        self.assertEqual(self.client.get("/api/tasks/999").status_code, 404)

    def test_create(self):
        response = self.client.post_json("/api/tasks", {"title": "Water the plants", "tags": "home"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["title"], "Water the plants")
        self.assertEqual(len(self.client.get("/api/tasks").json()), 11)
