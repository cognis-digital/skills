---
name: summarize
version: 1.0.0
description: Extractive summarizer that condenses a text or Markdown file to its most salient sentences. Use to compress long documents before reasoning over them.
entrypoint: run.py
runtime: python3
args:
  - name: file
    type: string
    required: true
    description: Path to the .txt or .md file to summarize.
  - name: sentences
    type: int
    required: false
    description: Number of sentences to return (default 5).
inputs: { stdin: false }
outputs: { format: json }
permissions: [filesystem, read-only]
tags: [nlp, summarize, text]
---

# summarize

A dependency-free extractive summarizer. Scores sentences by normalized word
frequency (TF over the document, stopwords removed) and returns the top-N
sentences in their original order. No model, no network.

## Usage

```bash
python3 run.py --file docs/LESSONS_INSIGHTS.md --sentences 4
```

## Output

```json
{
  "file": "docs/LESSONS_INSIGHTS.md",
  "original_sentences": 212,
  "summary_sentences": 4,
  "summary": "First salient sentence. Second. Third. Fourth."
}
```
