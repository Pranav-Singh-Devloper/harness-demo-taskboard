"""The web app: a small WSGI application serving HTML pages and a JSON API."""
import html
import json
import re
import traceback
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, quote

from . import db
from .dates import format_due, is_overdue, parse_due_date
from .export import to_csv
from .markdown import render_markdown
from .tags import join_tags, parse_tags

STYLESHEET = Path(__file__).resolve().parent.parent / "static" / "style.css"


class Request:
    def __init__(self, environ):
        self.method = environ["REQUEST_METHOD"]
        self.path = environ.get("PATH_INFO") or "/"
        self.query = {key: values[-1] for key, values in parse_qs(environ.get("QUERY_STRING", "")).items()}
        length = int(environ.get("CONTENT_LENGTH") or 0)
        self.body = environ["wsgi.input"].read(length) if length else b""

    @property
    def form(self):
        pairs = parse_qs(self.body.decode("utf-8"), keep_blank_values=True)
        return {key: values[-1] for key, values in pairs.items()}


class Response:
    def __init__(self, body="", status="200 OK", content_type="text/html; charset=utf-8", headers=()):
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.status = status
        self.headers = [("Content-Type", content_type), *headers]


def redirect(location):
    return Response("", "303 See Other", headers=[("Location", location)])


def json_response(data, status="200 OK"):
    return Response(json.dumps(data), status, "application/json")


def page(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · Taskboard</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header>
    <a class="brand" href="/">✅ Taskboard</a>
    <form class="search" action="/search" method="get">
      <input type="search" name="q" placeholder="Search tasks">
      <button>Search</button>
    </form>
    <a href="/export.csv">Export CSV</a>
  </header>
  <main>
{body}
  </main>
</body>
</html>"""


def not_found(message="Page not found"):
    return Response(page("Not found", f"<h1>{html.escape(message)}</h1>"), "404 Not Found")


def bad_request(message):
    return Response(page("Bad request", f"<h1>{html.escape(message)}</h1>"), "400 Bad Request")


def task_json(task):
    return {
        "id": task["id"],
        "title": task["title"],
        "description": task["description"],
        "due": task["due"],
        "priority": task["priority"],
        "tags": parse_tags(task["tags"]),
        "done": bool(task["done"]),
    }


def task_item(task, today):
    task_id = task["id"]
    badge = ' <span class="badge overdue">Overdue</span>' if is_overdue(task, today) else ""
    tags = " ".join(
        f'<a class="tag" href="/?tag={quote(tag)}">#{html.escape(tag)}</a>' for tag in parse_tags(task["tags"])
    )
    actions = []
    if not task["done"]:
        actions.append(f'<form method="post" action="/tasks/{task_id}/done"><button>Done</button></form>')
    actions.append(f'<form method="post" action="/tasks/{task_id}/delete"><button>Delete</button></form>')
    return f"""<li class="task priority-{task['priority']}">
  <a class="task-title" href="/tasks/{task_id}">{html.escape(task['title'])}</a>
  <span class="due">{format_due(task['due'], today)}</span>{badge}
  <span class="tags">{tags}</span>
  {' '.join(actions)}
</li>"""


def task_list(tasks, today, empty_message):
    if not tasks:
        return f'<p class="empty">{empty_message}</p>'
    return '<ul class="tasks">\n' + "\n".join(task_item(task, today) for task in tasks) + "\n</ul>"


NEW_TASK_FORM = """<h2>New task</h2>
<form class="new-task" method="post" action="/tasks">
  <input name="title" placeholder="Title" required>
  <textarea name="description" placeholder="Description (Markdown: **bold**, *italic*, `code`, [link](https://...))"></textarea>
  <label>Due <input type="date" name="due"></label>
  <label>Priority
    <select name="priority"><option>high</option><option selected>medium</option><option>low</option></select>
  </label>
  <input name="tags" placeholder="Tags, comma separated">
  <button>Add task</button>
</form>"""


class TaskboardApp:
    """WSGI application. `today` is a function returning the current date (tests pass a fixed one)."""

    def __init__(self, conn, today=date.today):
        self.conn = conn
        self.today = today
        self.routes = [
            ("GET", r"/", self.index),
            ("GET", r"/search", self.search),
            ("GET", r"/export\.csv", self.export),
            ("GET", r"/static/style\.css", self.stylesheet),
            ("GET", r"/tasks/(\d+)", self.show_task),
            ("POST", r"/tasks", self.create_task),
            ("POST", r"/tasks/(\d+)/done", self.complete_task),
            ("POST", r"/tasks/(\d+)/delete", self.delete_task),
            ("GET", r"/api/tasks", self.api_list),
            ("GET", r"/api/tasks/(\d+)", self.api_get),
            ("POST", r"/api/tasks", self.api_create),
        ]

    def __call__(self, environ, start_response):
        try:
            response = self.dispatch(Request(environ))
        except Exception:
            traceback.print_exc()
            response = Response("Internal Server Error", "500 Internal Server Error", "text/plain; charset=utf-8")
        start_response(response.status, response.headers)
        return [response.body]

    def dispatch(self, request):
        for method, pattern, handler in self.routes:
            match = re.fullmatch(pattern, request.path)
            if match and method == request.method:
                return handler(request, *(int(group) for group in match.groups()))
        return not_found()

    # Pages

    def index(self, request):
        tag = request.query.get("tag")
        tasks = db.list_tasks(self.conn, tag=tag)
        stats = db.progress(self.conn)
        today = self.today()
        heading = f"Tasks tagged #{html.escape(tag)}" if tag else "All tasks"
        body = f"""<h1>{heading}</h1>
<p class="progress">{stats['done']} of {stats['total']} done ({stats['percent']}%)</p>
{task_list([t for t in tasks if not t['done']], today, 'Nothing left to do.')}
<h2>Done</h2>
{task_list([t for t in tasks if t['done']], today, 'Nothing done yet.')}
{NEW_TASK_FORM}"""
        return Response(page("Tasks", body))

    def search(self, request):
        query = request.query.get("q", "").strip()
        results = db.search_tasks(self.conn, query) if query else []
        heading = f"<h1>Search results for “{html.escape(query)}”</h1>"
        return Response(page("Search", heading + "\n" + task_list(results, self.today(), "No matching tasks.")))

    def show_task(self, request, task_id):
        task = db.get_task(self.conn, task_id)
        if task is None:
            return not_found("Task not found")
        today = self.today()
        if task["done"]:
            status = "Done"
        elif is_overdue(task, today):
            status = "Overdue"
        else:
            status = "Open"
        due = format_due(task["due"], today) or "no due date"
        tags = ", ".join(html.escape(tag) for tag in parse_tags(task["tags"])) or "none"
        description = render_markdown(task["description"]) or "<em>No description.</em>"
        body = f"""<article class="task-detail">
<h1>{html.escape(task['title'])}</h1>
<p class="meta">{status} · due {due} · {task['priority']} priority · tags: {tags}</p>
<div class="description">{description}</div>
</article>"""
        return Response(page(task["title"], body))

    def export(self, request):
        return Response(
            to_csv(db.list_tasks(self.conn)),
            content_type="text/csv; charset=utf-8",
            headers=[("Content-Disposition", 'attachment; filename="tasks.csv"')],
        )

    def stylesheet(self, request):
        return Response(STYLESHEET.read_bytes(), content_type="text/css")

    # Form actions

    def create_task(self, request):
        form = request.form
        title = form.get("title", "").strip()
        if not title:
            return bad_request("A task needs a title")
        try:
            due = parse_due_date(form.get("due"))
        except ValueError:
            return bad_request("Invalid due date")
        priority = form.get("priority", "medium")
        if priority not in db.PRIORITIES:
            priority = "medium"
        db.add_task(
            self.conn,
            title=title,
            description=form.get("description", ""),
            due=due.isoformat() if due else None,
            priority=priority,
            tags=join_tags(parse_tags(form.get("tags", ""))),
        )
        return redirect("/")

    def complete_task(self, request, task_id):
        if db.get_task(self.conn, task_id) is None:
            return not_found("Task not found")
        db.set_done(self.conn, task_id)
        return redirect("/")

    def delete_task(self, request, task_id):
        tasks = db.list_tasks(self.conn)
        task = tasks[task_id - 1]
        db.delete_task(self.conn, task["id"])
        return redirect("/")

    # JSON API

    def api_list(self, request):
        return json_response([task_json(task) for task in db.list_tasks(self.conn)])

    def api_get(self, request, task_id):
        task = db.get_task(self.conn, task_id)
        if task is None:
            return json_response({"error": "Task not found"}, "404 Not Found")
        return json_response(task_json(task))

    def api_create(self, request):
        data = json.loads(request.body)
        due = parse_due_date(data.get("due"))
        task = db.add_task(
            self.conn,
            title=data["title"],
            description=data.get("description", ""),
            due=due.isoformat() if due else None,
            priority=data.get("priority", "medium"),
            tags=join_tags(parse_tags(data.get("tags", ""))),
        )
        return json_response(task_json(task), "201 Created")
