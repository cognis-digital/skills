#!/usr/bin/env python3
"""web-search skill: keyless DuckDuckGo + Google News RSS search."""
import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; cognis-skills/1.0; +https://cognis.digital)"


def _get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def ddg(query, limit):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    body = _get(url)
    out = []
    pat = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<u>[^"]+)"[^>]*>(?P<t>.*?)</a>'
        r'.*?<a[^>]*class="result__snippet"[^>]*>(?P<s>.*?)</a>',
        re.S,
    )
    for m in pat.finditer(body):
        raw = m.group("u")
        # DDG wraps target in a redirect param uddg=
        q = urllib.parse.urlparse(raw).query
        params = urllib.parse.parse_qs(q)
        target = params.get("uddg", [raw])[0]
        out.append(
            {
                "title": html.unescape(re.sub("<.*?>", "", m.group("t"))).strip(),
                "url": target,
                "snippet": html.unescape(re.sub("<.*?>", "", m.group("s"))).strip(),
                "source": "ddg",
            }
        )
        if len(out) >= limit:
            break
    return out


def gnews(query, limit):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    body = _get(url)
    out = []
    for m in re.finditer(r"<item>(.*?)</item>", body, re.S):
        block = m.group(1)
        t = re.search(r"<title>(.*?)</title>", block, re.S)
        lnk = re.search(r"<link>(.*?)</link>", block, re.S)
        d = re.search(r"<description>(.*?)</description>", block, re.S)
        if not (t and lnk):
            continue
        snippet_raw = d.group(1) if d else ""
        out.append(
            {
                "title": html.unescape(re.sub("<.*?>", "", t.group(1))).strip(),
                "url": lnk.group(1).strip(),
                "snippet": html.unescape(
                    re.sub("<.*?>", "", snippet_raw)
                ).strip(),
                "source": "gnews",
            }
        )
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--max", type=int, default=8)
    a = ap.parse_args()

    if not a.query.strip():
        sys.stderr.write("error: --query must not be empty\n")
        return 2
    if a.max < 1:
        sys.stderr.write("error: --max must be a positive integer\n")
        return 2

    results, errors, seen = [], [], set()
    for backend in (ddg, gnews):
        if len(results) >= a.max:
            break
        try:
            for r in backend(a.query, a.max):
                if r["url"] in seen:
                    continue
                seen.add(r["url"])
                results.append(r)
        except Exception as e:  # noqa: BLE001
            errors.append({"backend": backend.__name__, "error": str(e)})

    top = results[: a.max]
    payload = {"query": a.query, "count": len(top), "results": top}
    if errors:
        payload["errors"] = errors
    print(json.dumps(payload, indent=2))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
