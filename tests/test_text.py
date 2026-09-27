import unittest

from taskboard.export import to_csv
from taskboard.markdown import render_markdown
from taskboard.tags import join_tags, parse_tags


class TagsTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_tags(""), [])

    def test_single_tag(self):
        self.assertEqual(parse_tags("work"), ["work"])

    def test_several_tags(self):
        self.assertEqual(parse_tags("home,errands"), ["home", "errands"])

    def test_join(self):
        self.assertEqual(join_tags(["home", "errands"]), "home,errands")


class MarkdownTest(unittest.TestCase):
    def test_bold_and_italic(self):
        self.assertEqual(render_markdown("**a** and *b*"), "<strong>a</strong> and <em>b</em>")

    def test_code(self):
        self.assertEqual(render_markdown("run `make test`"), "run <code>make test</code>")

    def test_links(self):
        self.assertEqual(
            render_markdown("[brief](https://example.com/brief)"),
            '<a href="https://example.com/brief">brief</a>',
        )

    def test_html_is_escaped(self):
        self.assertEqual(render_markdown("<script>x</script>"), "&lt;script&gt;x&lt;/script&gt;")

    def test_newlines(self):
        self.assertEqual(render_markdown("a\nb"), "a<br>\nb")


class CsvTest(unittest.TestCase):
    def test_header_only(self):
        self.assertEqual(to_csv([]).splitlines(), ["id,title,due,priority,tags,done"])

    def test_simple_task(self):
        task = {"id": 1, "title": "Buy milk", "due": None, "priority": "low", "tags": "", "done": 0}
        self.assertEqual(to_csv([task]).splitlines()[1], "1,Buy milk,,low,,no")
