# tconv

I log my hours by hand in a plain text file because it's the fastest thing to
edit while I'm working. Payroll and invoicing tools want a CSV instead. Every
week I was doing that reformatting by hand, so this is a small converter that
does it for me.

Two formats, both round-trip:

- `csv` — one row per entry: `date,start,end,project,notes`
- `block` — one stanza per entry, `key: value` lines separated by blank lines,
  meant to be easy to type without lining up commas

## Usage

Convert a block-format log file to CSV:

```
$ tconv --from block --to csv timesheet.txt
date,start,end,project,notes
2026-09-08,09:00,12:30,acme,sprint planning
2026-09-08,13:15,17:00,acme,code review
```

Convert the other way, reading from stdin (piping works with either format):

```
$ cat timesheet.csv | tconv --from csv --to block
date: 2026-09-08
start: 09:00
end: 12:30
project: acme
notes: sprint planning

date: 2026-09-08
start: 13:15
end: 17:00
project: acme
notes: code review
```

Write to a file instead of stdout with `-o`:

```
$ tconv --from block --to csv timesheet.txt -o timesheet.csv
```

If you omit the input path (or pass `-` explicitly) tconv reads from stdin,
so it composes with other tools:

```
$ ssh work-vm cat timesheet.txt | tconv --from block --to csv -o timesheet.csv
```

## Block format

```
date: 2026-09-08
start: 09:00
end: 12:30
project: acme
notes: sprint planning
```

`date`, `start`, `end`, and `project` are required; `notes` is optional.
Times are `HH:MM` in whatever timezone you're already tracking in — tconv
doesn't do timezone conversion, it just moves the text between shapes.

## Running it without installing

```
$ python -m tconv --from csv --to block timesheet.csv
```

## Status

Early. No overnight-shift support yet (an entry's `end` must be later than
its `start` on the same day) and no rounding or summarization — it's a pure
reshaping tool for now.
