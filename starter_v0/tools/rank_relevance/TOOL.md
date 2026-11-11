---
name: rank_relevance
track: extension
kind: local_formatter
provider: local
requires_env: []
inputs: [items, query, limit]
outputs: [items, scores, item_count, returned_count]
side_effect: false
---
# rank_relevance

Rank existing objects by the number of distinct query tokens in `title` plus
`summary`. Apply Unicode casefold, then split at non-letter/non-number characters
(including underscores). Sort descending by score; preserve input order on ties.
Return up to `limit` items (default 5), including zero-score items when needed.
`scores` corresponds positionally to returned `items`; input is not modified.

Missing title/summary means empty text; present non-string fields are invalid.
A query with no tokens, a non-positive/non-integer limit (including bool), or
non-list/non-object input returns an error dict. Empty lists are valid.
Offline lexical overlap only: no semantic relevance or credibility claims.

Example: `rank_relevance([{"title": "AI AI"}, {"summary": "AI robotics"}], "AI robotics", 1)`
returns the second item with `scores=[2]`.
