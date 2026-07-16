"""Tests for livesearch pure/offline helpers (no network calls made)."""
from __future__ import annotations

import importlib.util
from datetime import timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_livesearch():
    spec = importlib.util.spec_from_file_location("livesearch_mod", ROOT / "livesearch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ls = _load_livesearch()


def test_google_news_rss_url_encodes_query_and_recency():
    url = ls.google_news_rss("oil sanctions", when="7d")
    assert url.startswith("https://news.google.com/rss/search?")
    assert "oil+sanctions" in url
    assert "when:7d" in url or "when%3A7d" in url


def test_parse_dt_rfc822():
    dt = ls._parse_dt("Wed, 02 Oct 2026 13:00:00 GMT")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 10 and dt.day == 2


def test_parse_dt_iso8601_z():
    dt = ls._parse_dt("2026-05-01T09:30:00Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).hour == 9


def test_parse_dt_none_and_garbage():
    assert ls._parse_dt(None) is None
    assert ls._parse_dt("") is None
    assert ls._parse_dt("not-a-date") is None


def test_fetch_feed_parses_rss(monkeypatch):
    rss = (
        b"<?xml version='1.0'?><rss><channel><title>Feed</title>"
        b"<item><title>Alpha &amp; Beta</title><link>https://x/1</link>"
        b"<pubDate>Wed, 02 Oct 2026 13:00:00 GMT</pubDate></item>"
        b"<item><title>Gamma</title><link>https://x/2</link>"
        b"<pubDate>Thu, 03 Oct 2026 09:00:00 GMT</pubDate></item>"
        b"</channel></rss>"
    )
    monkeypatch.setattr(ls, "_get", lambda url: rss)
    items = ls.fetch_feed("https://example/feed")
    assert len(items) == 2
    assert items[0]["title"] == "Alpha & Beta"  # html-unescaped
    assert items[0]["link"] == "https://x/1"
    assert items[0]["published"].endswith("Z")
    assert items[0]["source"] == "Feed"


def test_fetch_feed_atom(monkeypatch):
    atom = (
        b"<?xml version='1.0'?>"
        b"<feed xmlns='http://www.w3.org/2005/Atom'><title>AtomFeed</title>"
        b"<entry><title>Entry One</title>"
        b"<link href='https://a/1'/>"
        b"<updated>2026-05-01T09:30:00Z</updated></entry></feed>"
    )
    monkeypatch.setattr(ls, "_get", lambda url: atom)
    items = ls.fetch_feed("https://example/atom")
    assert len(items) == 1
    assert items[0]["title"] == "Entry One"
    assert items[0]["link"] == "https://a/1"


def test_fetch_feed_bad_xml_returns_empty(monkeypatch):
    monkeypatch.setattr(ls, "_get", lambda url: b"<<not xml")
    assert ls.fetch_feed("https://example/bad") == []


def test_harvest_dedupes_and_filters_old(monkeypatch):
    feed_a = [
        {"title": "New", "link": "https://x/1", "published": "2026-06-01T00:00:00Z",
         "source": "a", "query": ""},
        {"title": "Dup", "link": "https://x/1", "published": "2026-06-02T00:00:00Z",
         "source": "a", "query": ""},
        {"title": "Old", "link": "https://x/9", "published": "2020-01-01T00:00:00Z",
         "source": "a", "query": ""},
    ]
    monkeypatch.setattr(ls, "fetch_feed",
                        lambda url, limit=50, source="": list(feed_a))
    out = ls.harvest(["https://example/feed"], since_days=0, min_year=2026)
    links = [i["link"] for i in out]
    assert links.count("https://x/1") == 1  # de-duped
    assert "https://x/9" not in links  # min_year filter drops 2020
