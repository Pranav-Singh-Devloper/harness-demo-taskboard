"""CSV export of the task list."""

HEADER = ["id", "title", "due", "priority", "tags", "done"]


def to_csv(tasks):
    lines = [",".join(HEADER)]
    for task in tasks:
        row = [
            str(task["id"]),
            task["title"],
            task["due"] or "",
            task["priority"],
            task["tags"],
            "yes" if task["done"] else "no",
        ]
        lines.append(",".join(row))
    return "\n".join(lines) + "\n"
