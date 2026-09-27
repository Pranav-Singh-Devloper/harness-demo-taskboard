# Taskboard

A tiny to-do web app that uses only the Python standard library (`wsgiref` and `sqlite3`). There is nothing to install.

## Run it

Requires Python 3.9 or newer.

```bash
python3 app.py
```

Then open http://127.0.0.1:8000. The first run creates `tasks.db` with some sample tasks (`--db` picks another file, `--port` another port).

## Run the tests

```bash
python3 -m unittest
```

## Features

- A board of open and done tasks, with due dates, an "Overdue" badge and overall progress
- Task pages whose descriptions support a little Markdown: `**bold**`, `*italic*`, `` `code` `` and `[links](https://example.com)`
- Search by title (`/search?q=...`) and filter by tag (`/?tag=work`)
- CSV export at `/export.csv`
- A JSON API:

| Method | URL | What it does |
|---|---|---|
| `GET` | `/api/tasks` | All tasks |
| `GET` | `/api/tasks/<id>` | One task |
| `POST` | `/api/tasks` | Create a task from JSON: `title` (required), `description`, `due` (`YYYY-MM-DD`), `priority` (`high`, `medium` or `low`), `tags` (comma-separated) |

## Project layout

```
app.py                  Runs the app with wsgiref
taskboard/web.py        WSGI app: routing, pages, form actions and the JSON API
taskboard/db.py         SQLite storage and queries
taskboard/dates.py      Due-date parsing, overdue check and formatting
taskboard/tags.py       Tag parsing
taskboard/markdown.py   Markdown subset for descriptions
taskboard/export.py     CSV export
data/seed.json          Sample tasks
static/style.css        Styles
tests/                  unittest suite (tests/helpers.py has a small WSGI test client)
```
