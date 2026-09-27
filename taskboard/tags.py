"""Task tags, stored as a comma-separated string."""


def parse_tags(text):
    """Split the comma-separated tags typed in the form into a list."""
    if not text:
        return []
    return text.split(",")


def join_tags(tags):
    return ",".join(tags)
