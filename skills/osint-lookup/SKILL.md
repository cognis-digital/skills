---
name: osint-lookup
version: 1.0.0
description: Resolve a domain or host to public footprint signals - DNS A/AAAA/MX/TXT records, resolved IPs, and reverse-DNS hints. Use for passive recon on a target.
entrypoint: run.py
runtime: python3
args:
  - name: host
    type: string
    required: true
    description: Domain or hostname to look up (e.g. cognis.digital).
inputs: { stdin: false }
outputs: { format: json }
permissions: [network]
tags: [osint, recon, network]
---

# osint-lookup

Passive, read-only reconnaissance on a hostname. Uses the stdlib `socket`
resolver plus DNS-over-HTTPS (Google DoH) to gather A/AAAA/MX/TXT/NS records,
then reverse-resolves the A records for PTR hints. No port scanning, no
intrusive probing — strictly public DNS data.

## Usage

```bash
python3 run.py --host cognis.digital
```

## Output

```json
{
  "host": "cognis.digital",
  "ips": ["203.0.113.10"],
  "records": {"A": ["203.0.113.10"], "MX": ["10 mail.cognis.digital"], "TXT": ["v=spf1 ..."]},
  "reverse": {"203.0.113.10": "server.example.net"}
}
```

## Notes

DoH failures fall back to the system resolver for A/AAAA. Errors are reported in
an `errors` array; the skill never invents records.
