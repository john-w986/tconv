from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

CSV_FIELDS = ["date", "start", "end", "project", "notes"]
REQUIRED_FIELDS = ("date", "start", "end", "project")


class FormatError(ValueError):
    """Raised when input text doesn't match the format it's supposed to be."""


@dataclass
class TimeEntry:
    date: str
    start: str
    end: str
    project: str
    notes: str = ""

    def hours(self) -> float:
        fmt = "%Y-%m-%d %H:%M"
        started = datetime.strptime(f"{self.date} {self.start}", fmt)
        ended = datetime.strptime(f"{self.date} {self.end}", fmt)
        if ended <= started:
            # overnight shifts aren't supported yet, so treat this as bad data
            raise FormatError(
                f"entry on {self.date} ends at or before it starts "
                f"({self.start}-{self.end})"
            )
        return (ended - started).total_seconds() / 3600


def _validate(entry: TimeEntry, where: str) -> None:
    missing = [f for f in REQUIRED_FIELDS if not getattr(entry, f)]
    if missing:
        raise FormatError(f"{where}: missing required field(s): {', '.join(missing)}")


def parse_csv(text: str) -> list[TimeEntry]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return []
    missing = [f for f in REQUIRED_FIELDS if f not in reader.fieldnames]
    if missing:
        raise FormatError(f"csv is missing required column(s): {', '.join(missing)}")

    entries = []
    for line_no, row in enumerate(reader, start=2):
        entry = TimeEntry(
            date=(row.get("date") or "").strip(),
            start=(row.get("start") or "").strip(),
            end=(row.get("end") or "").strip(),
            project=(row.get("project") or "").strip(),
            notes=(row.get("notes") or "").strip(),
        )
        _validate(entry, where=f"csv line {line_no}")
        entries.append(entry)
    return entries


def write_csv(entries: list[TimeEntry]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for entry in entries:
        writer.writerow(
            {
                "date": entry.date,
                "start": entry.start,
                "end": entry.end,
                "project": entry.project,
                "notes": entry.notes,
            }
        )
    return out.getvalue()


def parse_block(text: str) -> list[TimeEntry]:
    """Block format: one entry per stanza, "key: value" lines, blank line between entries.

    Example:
        date: 2026-09-08
        start: 09:00
        end: 12:30
        project: acme
        notes: sprint planning
    """
    entries: list[TimeEntry] = []
    record: dict[str, str] = {}
    record_start_line = 1

    def flush() -> None:
        if not record:
            return
        entry = TimeEntry(
            date=record.get("date", ""),
            start=record.get("start", ""),
            end=record.get("end", ""),
            project=record.get("project", ""),
            notes=record.get("notes", ""),
        )
        _validate(entry, where=f"block entry starting at line {record_start_line}")
        entries.append(entry)
        record.clear()

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if not record:
            record_start_line = line_no
        if ":" not in line:
            raise FormatError(f"line {line_no}: expected 'key: value', got {raw_line!r}")
        key, _, value = line.partition(":")
        key = key.strip().lower()
        if key not in (*REQUIRED_FIELDS, "notes"):
            raise FormatError(f"line {line_no}: unknown field {key!r}")
        record[key] = value.strip()
    flush()
    return entries


def write_block(entries: list[TimeEntry]) -> str:
    stanzas = []
    for entry in entries:
        lines = [
            f"date: {entry.date}",
            f"start: {entry.start}",
            f"end: {entry.end}",
            f"project: {entry.project}",
        ]
        if entry.notes:
            lines.append(f"notes: {entry.notes}")
        stanzas.append("\n".join(lines))
    if not stanzas:
        return ""
    return "\n\n".join(stanzas) + "\n"
