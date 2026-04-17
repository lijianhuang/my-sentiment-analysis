"""
app.py  —  Streamlit dashboard for parsed buzzing topics JSON

Usage:
    streamlit run app.py
    streamlit run app.py -- --folder ./reports
    streamlit run app.py -- --report path/to/file.json
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Sentiment", page_icon="📡", layout="centered")

SENTIMENT_COLOR = {"positive": "green", "negative": "red", "neutral": "gray", "mixed": "orange"}

@st.cache_data
def load_report(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def find_latest_report(folder: Path):
    pattern = re.compile(r"UOB_Malaysia_BUZZ_(\d{4}-\d{2}-\d{2})_(\d{4})_parsed\.json$", re.IGNORECASE)
    candidates = []
    for f in folder.glob("UOB_Malaysia_BUZZ_*_parsed.json"):
        m = pattern.search(f.name)
        if m:
            ts = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H%M")
            candidates.append((ts, f))
    return sorted(candidates, reverse=True)[0][1] if candidates else None

parser = argparse.ArgumentParser()
parser.add_argument("--report", default=None)
parser.add_argument("--folder", default=".")
args, _ = parser.parse_known_args()

if args.report:
    report_path = Path(args.report)
    if not report_path.exists():
        st.error(f"Report not found: `{report_path}`")
        st.stop()
else:
    report_path = find_latest_report(Path(args.folder))
    if not report_path:
        st.error("No parsed report found. Run `parse_report.py` first.")
        st.stop()

report = load_report(str(report_path))
topics = report["topics"]

# ── Header ──────────────────────────────────────────────────────────────────
st.title(f"{report['brand']} — Sentiment Summary")
st.caption(f"{report['period_start']} → {report['period_end']}")

st.divider()

# ── Topics overview ──────────────────────────────────────────────────────────
st.subheader("Topics Discussed")
for t in topics:
    st.write(f"{t['id']}. **{t['title']}** — {t['sentiment'].title()}, Hotness {t['hotness']}/10")

st.divider()

# ── Each topic ───────────────────────────────────────────────────────────────
for t in topics:
    color = SENTIMENT_COLOR[t["sentiment"]]
    st.subheader(f"{t['id']}. {t['title']}")
    st.caption(f"**Theme:** {t['theme']}  |  :{color}[ {t['sentiment'].title()}]  |   Hotness {t['hotness']}/10 — {t['hotness_rationale']}")

    st.write(t["summary"])

    if t["key_complaints"] or t["key_praises"]:
        col_c, col_p = st.columns(2)
        with col_c:
            if t["key_complaints"]:
                st.markdown("**🔴 Complaints**")
                for c in t["key_complaints"]:
                    st.write(f"- {c}")
        with col_p:
            if t["key_praises"]:
                st.markdown("**🟢 Praises**")
                for p in t["key_praises"]:
                    st.write(f"- {p}")

    if t.get("representative_quotes"):
        st.markdown("**💬 Quotes**")
        for q in t["representative_quotes"]:
            st.info(f'"{q["text"]}" — *{q["source"]}*')

    if t.get("sources"):
        st.markdown("**Sources**")
        for s in t["sources"]:
            if s.get("url"):
                st.caption(f"{s['platform']}: {s['url']}")
            else:
                st.caption(s["platform"])

    if t.get("tags"):
        st.caption("Tags: " + "  ".join(f"`#{tag}`" for tag in t["tags"]))

    st.divider()

if report.get("analyst_notes"):
    st.caption(f"📝 {report['analyst_notes']}")