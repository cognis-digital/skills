#!/usr/bin/env python3
"""summarize skill: frequency-based extractive summarizer (stdlib only)."""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

STOPWORDS = set(
    """a an and are as at be by for from has have in is it its of on or that the
    to was were will with this these those they them their he she you your we our
    not but if then than so such can could would should may might do does did
    """.split()
)


def split_sentences(text):
    # strip markdown headers/code fences first
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#>*`_\[\]]", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if len(s.strip()) > 20]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--sentences", type=int, default=5)
    a = ap.parse_args()

    p = Path(a.file)
    if not p.is_file():
        print(json.dumps({"error": f"file not found: {a.file}"}))
        return 2

    text = p.read_text(encoding="utf-8", errors="replace")
    sentences = split_sentences(text)
    if not sentences:
        print(json.dumps({"error": "no extractable sentences"}))
        return 1

    words = [w for w in re.findall(r"[a-zA-Z]{3,}", text.lower()) if w not in STOPWORDS]
    freq = Counter(words)
    if not freq:
        top = sentences[: a.sentences]
    else:
        maxf = max(freq.values())
        norm = {w: c / maxf for w, c in freq.items()}
        scored = []
        for idx, s in enumerate(sentences):
            toks = [w for w in re.findall(r"[a-zA-Z]{3,}", s.lower()) if w in norm]
            score = sum(norm[w] for w in toks) / (len(toks) + 1)
            scored.append((score, idx, s))
        scored.sort(reverse=True)
        chosen = sorted(scored[: a.sentences], key=lambda x: x[1])
        top = [s for _, _, s in chosen]

    out = {
        "file": a.file,
        "original_sentences": len(sentences),
        "summary_sentences": len(top),
        "summary": " ".join(top),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
