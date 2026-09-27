import unittest
from datetime import date

from taskboard.dates import format_due, is_overdue, parse_due_date

TODAY = date(2026, 10, 1)


class ParseDueDateTest(unittest.TestCase):
    def test_empty_means_no_due_date(self):
        self.assertIsNone(parse_due_date(""))
        self.assertIsNone(parse_due_date(None))

    def test_first_of_january(self):
        self.assertEqual(parse_due_date("2026-01-01"), date(2026, 1, 1))

    def test_rejects_text(self):
        with self.assertRaises(ValueError):
            parse_due_date("next tuesday")


class IsOverdueTest(unittest.TestCase):
    def test_past_due_date_is_overdue(self):
        self.assertTrue(is_overdue({"done": 0, "due": "2026-09-28"}, TODAY))

    def test_future_due_date_is_not_overdue(self):
        self.assertFalse(is_overdue({"done": 0, "due": "2026-10-05"}, TODAY))

    def test_done_tasks_are_never_overdue(self):
        self.assertFalse(is_overdue({"done": 1, "due": "2026-09-28"}, TODAY))

    def test_no_due_date(self):
        self.assertFalse(is_overdue({"done": 0, "due": None}, TODAY))


class FormatDueTest(unittest.TestCase):
    def test_today_and_tomorrow(self):
        self.assertEqual(format_due("2026-10-01", TODAY), "today")
        self.assertEqual(format_due("2026-10-02", TODAY), "tomorrow")

    def test_other_days(self):
        self.assertEqual(format_due("2026-10-05", TODAY), "Mon 5 Oct")

    def test_no_due_date(self):
        self.assertEqual(format_due(None, TODAY), "")
