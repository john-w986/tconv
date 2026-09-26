from __future__ import annotations

import unittest

from tconv.core import (
    FormatError,
    TimeEntry,
    parse_block,
    parse_csv,
    round_hours,
    sum_hours_by_project,
    write_block,
    write_csv,
    write_summary,
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

    def test_hours_handles_overnight_shift(self):
        entry = TimeEntry(date="2026-09-08", start="22:00", end="06:00", project="acme")
        self.assertEqual(entry.hours(), 8.0)

    def test_hours_rejects_zero_length_shift(self):
        entry = TimeEntry(date="2026-09-08", start="09:00", end="09:00", project="acme")
        with self.assertRaises(FormatError):
            entry.hours()


class SummaryTests(unittest.TestCase):
    def test_sum_hours_by_project_groups_and_adds(self):
        totals = sum_hours_by_project(SAMPLE_ENTRIES)
        self.assertEqual(totals, {"acme": 7.25})

    def test_sum_hours_by_project_keeps_projects_separate(self):
        entries = [
            TimeEntry(date="2026-09-08", start="09:00", end="10:00", project="acme"),
            TimeEntry(date="2026-09-08", start="10:00", end="10:30", project="beta"),
        ]
        totals = sum_hours_by_project(entries)
        self.assertEqual(totals, {"acme": 1.0, "beta": 0.5})

    def test_write_summary_empty_input_gives_empty_string(self):
        self.assertEqual(write_summary([]), "")

    def test_write_summary_sorts_projects_and_adds_total(self):
        entries = [
            TimeEntry(date="2026-09-08", start="09:00", end="10:00", project="zeta"),
            TimeEntry(date="2026-09-08", start="10:00", end="10:30", project="acme"),
        ]
        self.assertEqual(
            write_summary(entries),
            "acme: 0.50\nzeta: 1.00\ntotal: 1.50\n",
        )


class RoundHoursTests(unittest.TestCase):
    def test_round_hours_rounds_to_nearest_quarter(self):
        self.assertEqual(round_hours(1.1), 1.0)
        self.assertEqual(round_hours(1.2), 1.25)
        self.assertEqual(round_hours(1.4), 1.5)

    def test_round_hours_custom_increment(self):
        self.assertEqual(round_hours(1.2, increment=0.5), 1.0)
        self.assertEqual(round_hours(1.3, increment=0.5), 1.5)

    def test_sum_hours_by_project_rounds_per_entry_before_adding(self):
        entries = [
            TimeEntry(date="2026-09-08", start="09:00", end="09:52", project="acme"),
            TimeEntry(date="2026-09-08", start="10:00", end="10:52", project="acme"),
        ]
        # each entry is 0.8667h, rounds to 0.75h alone; unrounded total would
        # be 1.7333h which rounds to 1.75h, so per-entry rounding must be
        # taking effect rather than rounding the combined total
        totals = sum_hours_by_project(entries, round_quarter=True)
        self.assertEqual(totals, {"acme": 1.5})

    def test_write_summary_round_quarter(self):
        entries = [
            TimeEntry(date="2026-09-08", start="09:00", end="09:52", project="acme"),
        ]
        self.assertEqual(
            write_summary(entries, round_quarter=True),
            "acme: 0.75\ntotal: 0.75\n",
        )


if __name__ == "__main__":
    unittest.main()
