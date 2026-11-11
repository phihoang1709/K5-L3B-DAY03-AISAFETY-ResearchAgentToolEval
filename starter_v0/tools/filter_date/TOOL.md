---
name: filter_date
track: extension
kind: local_formatter
provider: local
requires_env: []
inputs: [items, start_date, end_date]
outputs: [items, item_count, kept_count, invalid_date_count, out_of_range_count, dropped_count]
side_effect: false
---
# filter_date

Filter existing objects by their explicit `date` field, including both endpoints.
All dates must be real calendar dates in exactly `YYYY-MM-DD` format. Preserve
input order without modifying input. Missing/invalid item dates are dropped and
counted in `invalid_date_count`; valid dates outside the range are counted in
`out_of_range_count`. `dropped_count` is their sum. Empty input is valid.

An invalid/reversed range or a non-list/non-object input returns an error dict.
Never infer dates from titles, URLs or search context. Offline; no API calls.

Example: `filter_date([{"date": "2024-02-29"}, {}], "2024-02-01", "2024-02-29")`
keeps the first item and returns `invalid_date_count=1`.
