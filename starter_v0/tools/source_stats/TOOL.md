---
name: source_stats
track: extension
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [sources, item_count, valid_url_count, missing_url_count, invalid_url_count]
side_effect: false
---
# source_stats

Count existing items by lowercase hostname from syntactically valid HTTP(S) URLs.
Ignore scheme, path and port when grouping. Subdomains remain distinct. Do not
deduplicate items, resolve DNS or assess source credibility. Input is not modified.

Absent/null/blank URLs count as missing; non-string URLs, unsupported schemes,
missing or malformed hosts/ports, whitespace/control characters count as invalid.
DNS labels (including IDNA-compatible Unicode), localhost and IPv6 are supported;
the output key retains the lowercase hostname as provided, including a trailing
dot if present. No network requests. Empty lists are valid; non-list inputs or
non-object members return an error dict.

Example: `source_stats([{"url": "https://EXAMPLE.com/a"}, {}])` returns
`sources={"example.com": 1}`, `missing_url_count=1`, `invalid_url_count=0`.
