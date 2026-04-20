"""
parse_report.py
---------------
Auto-detects the latest UOB_Thailand_Q1_REPORT_*.txt in a folder, calls OpenAI
to extract structured data, validates with Pydantic, writes JSON.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

load_dotenv()
from schema import BuzzingTopicsReport

# ── File pattern updated for Thailand Q1 ──────────────────────────────────────

FILE_PATTERN = re.compile(
    r"UOB_Thailand_Q1_REPORT_(\d{4}-\d{2}-\d{2})_(\d{4})\.txt$",
    re.IGNORECASE
)

def find_latest(folder: Path) -> Path:
    """Return the most recent UOB_Thailand_Q1_REPORT_*.txt in folder by filename timestamp."""
    candidates = []
    for f in folder.glob("UOB_Thailand_Q1_REPORT_*.txt"):
        m = FILE_PATTERN.search(f.name)
        if m:
            date_str, time_str = m.group(1), m.group(2)
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M")
            candidates.append((ts, f))

    if not candidates:
        print(f"No files matching UOB_Thailand_Q1_REPORT_YYYY-MM-DD_HHMM.txt found in: {folder}")
        sys.exit(1)

    candidates.sort(reverse=True)
    latest_ts, latest_file = candidates[0]

    if len(candidates) > 1:
        print(f"Found {len(candidates)} matching files. Using latest:")
    print(f"  → {latest_file.name}  ({latest_ts.strftime('%Y-%m-%d %H:%M')})")
    return latest_file

# ── Prompt updated for Thai Platforms ─────────────────────────────────────────

SYSTEM_PROMPT = """You are a structured data extraction assistant.
You receive a raw social-listening / buzzing-topics report and return ONLY
a single valid JSON object — no markdown fences, no commentary, no preamble.

The JSON must conform exactly to this schema:

{
  "brand": str,
  "generated_at": str (ISO 8601),
  "period_start": str (YYYY-MM-DD),
  "period_end": str (YYYY-MM-DD),
  "sources_monitored": [str, ...],
  "total_topics": int,
  "analyst_notes": str,
  "topics": [
    {
      "id": int,
      "theme": str,
      "title": str,
      "hotness": int,
      "hotness_rationale": str,
      "sentiment": "positive" | "negative" | "neutral" | "mixed",
      "sentiment_score": float,
      "summary": str,
      "key_complaints": [str, ...],
      "key_praises": [str, ...],
      "representative_quotes": [{ "text": str, "source": str }],
      "sources": [{ "platform": str, "url": str | null }, ...],  // extract URLs exactly as they appear in the report text
      "tags": [str, ...]
    }
  ]
}

Hotness 1-10: 9-10 viral, 7-8 very active, 5-6 active, 3-4 moderate, 1-2 low.
Sentiment score: -1.0 to +1.0.
Max 2 representative_quotes per topic. Prefix paraphrases with "~".
Thai platform examples: Pantip, Facebook, Chaimiles, Money Buffalo.
"""

# ── Parse ─────────────────────────────────────────────────────────────────────

def parse_report(raw_text: str) -> BuzzingTopicsReport:
    client = OpenAI()

    print("Calling OpenAI API (gpt-5.4-mini, reasoning=high)...")
    response = client.responses.create(
        model="gpt-5.4-mini",
        reasoning={"effort": "high"},
        input=[
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\nExtract structured JSON from this report:\n\n{raw_text}"}
        ]
    )

    raw_json_str = response.output_text.strip()
    # Strip markdown fences if present
    if raw_json_str.startswith("```"):
        raw_json_str = raw_json_str.split("```")[1].lstrip("json").strip()
    print("API call successful. Validating schema...")

    try:
        data = json.loads(raw_json_str)
        report = BuzzingTopicsReport(**data)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"Pydantic validation error:\n{e}")
        sys.exit(1)

    return report   

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default=".", help="Folder to scan for latest report (default: current dir)")
    parser.add_argument("--input",  default=None, help="Explicit input file (skips auto-detect)")
    parser.add_argument("--output", default=None, help="Output JSON path (default: same name as input + _parsed.json)")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Input file not found: {input_path}")
            sys.exit(1)
    else:
        input_path = find_latest(Path(args.folder))

    raw_text = input_path.read_text(encoding="utf-8")
    report = parse_report(raw_text)

    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "_parsed.json")
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    print(f"Saved → {output_path}")
    for t in report.topics:
        print(f"  [{t.id}] {t.theme:30s} hotness={t.hotness}/10  sentiment={t.sentiment}")


if __name__ == "__main__":
    main()