---
name: web-search
version: 1.0.0
description: Keyless web/news search returning ranked result titles, urls, and snippets. Use when the agent needs current external information it does not already have.
entrypoint: run.py
runtime: python3
args:
  - name: query
    type: string
    required: true
    description: Search query string.
  - name: max
    type: int
    required: false
    description: Maximum results to return (default 8).
inputs: { stdin: false }
outputs: { format: json }
permissions: [network]
tags: [research, osint, web]
---

# web-search

Runs a keyless web search against DuckDuckGo's HTML endpoint with a Google-News RSS
fallback. Returns a ranked, deduplicated list of `{title, url, snippet, source}`.

Designed for the OSINT firm and ATD research path where no paid API key is available.

## Usage

```bash
python3 run.py --query "uranium export controls 2026" --max 6
```

## Output

```json
{
  "query": "uranium export controls 2026",
  "count": 6,
  "results": [
    {"title": "...", "url": "https://...", "snippet": "...", "source": "ddg"}
  ]
}
```

## Notes

- Round-robins backends so a single throttled endpoint does not starve results.
- Network failures degrade gracefully: returns whatever backend succeeded, with
  `errors` listing the rest. Never fabricates results.
