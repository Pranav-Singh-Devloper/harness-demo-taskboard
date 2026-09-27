"""A very small Markdown subset for task descriptions: **bold**, *italic*, `code` and [links](url)."""
import html
import re

LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"\*(.+?)\*")
CODE = re.compile(r"`([^`]+)`")


def render_markdown(text):
    """Render a description as HTML. The text is escaped first, so raw HTML never gets through."""
    out = html.escape(text)
    out = CODE.sub(r"<code>\1</code>", out)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = ITALIC.sub(r"<em>\1</em>", out)
    out = LINK.sub(r'<a href="\2">\1</a>', out)
    return out.replace("\n", "<br>\n")
