---
name: dedupe
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [items, item_count, unique_count, duplicates_removed]
side_effect: false
---
# dedupe

Removes duplicate research items from an existing list while preserving the
first item and the original order. It uses a normalized URL when available and
falls back to a normalized title. It does not search the web or infer missing
content.
