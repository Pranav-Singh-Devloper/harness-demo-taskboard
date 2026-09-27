"""Run the task board locally: python3 app.py [--port 8000] [--db tasks.db]"""
import argparse
from wsgiref.simple_server import make_server

from taskboard.db import connect
from taskboard.web import TaskboardApp


def main():
    parser = argparse.ArgumentParser(description="Run the Taskboard web app.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="tasks.db", help="SQLite file, created with sample tasks on first run")
    args = parser.parse_args()

    app = TaskboardApp(connect(args.db))
    with make_server("127.0.0.1", args.port, app) as server:
        print(f"Taskboard running at http://127.0.0.1:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
