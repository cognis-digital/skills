#!/usr/bin/env python3
"""osint-lookup skill: passive DNS footprint via DoH + stdlib resolver."""
import argparse
import json
import socket
import sys
import urllib.parse
import urllib.request

DOH = "https://dns.google/resolve?"
RR_TYPES = ["A", "AAAA", "MX", "TXT", "NS"]


def doh_query(host, rtype):
    url = DOH + urllib.parse.urlencode({"name": host, "type": rtype})
    req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [a.get("data", "").strip('"') for a in data.get("Answer", []) if "data" in a]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    a = ap.parse_args()
    host = a.host.strip().lower()

    records, errors = {}, []
    for rtype in RR_TYPES:
        try:
            vals = doh_query(host, rtype)
            if vals:
                records[rtype] = vals
        except Exception as e:  # noqa: BLE001
            errors.append({"type": rtype, "error": str(e)})

    ips = list(records.get("A", []))
    if not ips:
        # fallback to system resolver
        try:
            infos = socket.getaddrinfo(host, None)
            ips = sorted({i[4][0] for i in infos if ":" not in i[4][0]})
            if ips:
                records.setdefault("A", ips)
        except OSError as e:
            errors.append({"type": "A-fallback", "error": str(e)})

    reverse = {}
    for ip in ips[:8]:
        try:
            reverse[ip] = socket.gethostbyaddr(ip)[0]
        except OSError:
            reverse[ip] = None

    out = {
        "host": host,
        "ips": ips,
        "records": records,
        "reverse": reverse,
    }
    if errors:
        out["errors"] = errors
    print(json.dumps(out, indent=2))
    return 0 if (records or ips) else 1


if __name__ == "__main__":
    sys.exit(main())
