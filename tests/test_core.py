from __future__ import annotations

import unittest

from tconv.core import (
    FormatError,
    TimeEntry,
    parse_block,
    parse_csv,
    write_block,
    write_csv,
)

SAMPLE_ENTRIES = [
    TimeEntry(
        date="2026-09-08",
        start="09:00",
        end="12:30",
        project="acme",
        notes="sprint planning",
    ),
    TimeEntry(
        date="2026-09-08",
        start="13:15",
        end="17:00",
        project="acme",
        notes="",
    ),
]


class CsvRoundTripTests(unittest.TestCase):
    def test_write_then_parse_gives_back_same_entries(self):
        csv_text = write_csv(SAMPLE_ENTRIES)
        self.assertEqual(parse_csv(csv_text), SAMPLE_ENTRIES)

    def test_parse_csv_strips_surrounding_whitespace(self):
        csv_text = (
            "date,start,end,project,notes\n"
            " 2026-09-08 , 09:00 , 12:30 , acme , sprint planning \n"
        )
        entries = parse_csv(csv_text)
        self.assertEqual(entries[0].date, "2026-09-08")
        self.assertEqual(entries[0].notes, "sprint planning")

    def test_parse_csv_empty_input_gives_no_entries(self):
        self.assertEqual(parse_csv(""), [])

    def test_parse_csv_missing_column_raises(self):
        with self.assertRaises(FormatError):
            parse_csv("date,start,end,notes\n2026-09-08,09:00,12:30,x\n")

    def test_parse_csv_missing_required_value_raises(self):
        with self.assertRaises(FormatError):
            parse_csv("date,start,end,project,notes\n2026-09-08,,12:30,acme,\n")


class BlockRoundTripTests(unittest.TestCase):
    def test_write_then_parse_gives_back_same_entries(self):
        block_text = write_block(SAMPLE_ENTRIES)
        self.assertEqual(parse_block(block_text), SAMPLE_ENTRIES)

    def test_parse_block_empty_input_gives_no_entries(self):
        self.assertEqual(parse_block(""), [])

    def test_parse_block_omits_empty_notes_line(self):
        block_text = write_block(SAMPLE_ENTRIES)
        self.assertNotIn("notes: \n", block_text)

    def test_parse_block_unknown_field_raises(self):
        with self.assertRaises(FormatError):
            parse_block("date: 2026-09-08\nstart: 09:00\nend: 12:30\nproject: acme\nteam: x\n")

    def test_parse_block_missing_required_field_raises(self):
        with self.assertRaises(FormatError):
            parse_block("date: 2026-09-08\nstart: 09:00\nproject: acme\n")

    def test_parse_block_bad_line_raises(self):
        with self.assertRaises(FormatError):
            parse_block("date 2026-09-08\n")


class CrossFormatRoundTripTests(unittest.TestCase):
    def test_csv_to_block_to_csv(self):
        csv_text = write_csv(SAMPLE_ENTRIES)
        entries = parse_csv(csv_text)
        block_text = write_block(entries)
        self.assertEqual(parse_block(block_text), SAMPLE_ENTRIES)

    def test_block_to_csv_to_block(self):
        block_text = write_block(SAMPLE_ENTRIES)
        entries = parse_block(block_text)
        csv_text = write_csv(entries)
        self.assertEqual(parse_csv(csv_text), SAMPLE_ENTRIES)


class HoursTests(unittest.TestCase):
    def test_hours_computes_duration(self):
        entry = TimeEntry(date="2026-09-08", start="09:00", end="12:30", project="acme")
        self.assertEqual(entry.hours(), 3.5)

    def test_hours_rejects_end_before_start(self):
        entry = TimeEntry(date="2026-09-08", start="17:00", end="09:00", project="acme")
        with self.assertRaises(FormatError):
            entry.hours()


if __name__ == "__main__":
    unittest.main()
