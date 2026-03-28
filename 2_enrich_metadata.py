"""
Step 2 — Enrich video metadata using the YouTube Data API v3.

Fetches channel name, publish date, duration, and tags for each video
exported in step 1. Videos are processed in batches of 50 (API maximum).

Requirements:
    pip install requests

Usage:
    python3 2_enrich_metadata.py --api-key YOUR_API_KEY

Output:
    enriched.json — list of videos with full metadata
"""

import csv
import json
import sys
import time
import re
import argparse

import requests


# ── Configuration ────────────────────────────────────────────────────────────

INPUT_CSV   = "watch_later_public.csv"
OUTPUT_JSON = "enriched.json"
BATCH_SIZE  = 50
SLEEP_SEC   = 0.1   # between API calls


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_duration(iso: str) -> str:
    """Convert ISO 8601 duration (PT4M13S) to human-readable (4:13)."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return ""
    h, mn, s = (int(x) if x else 0 for x in m.groups())
    if h:
        return f"{h}:{mn:02d}:{s:02d}"
    return f"{mn}:{s:02d}"


def fetch_batch(ids: list, api_key: str) -> dict:
    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet,contentDetails",
            "id": ",".join(ids),
            "key": api_key,
        },
        timeout=15,
    )
    data = resp.json()
    if "error" in data:
        print(f"\n❌ API error: {data['error']['message']}", file=sys.stderr)
        sys.exit(1)
    return data


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Enrich Watch Later metadata.")
    parser.add_argument("--api-key", required=True, help="YouTube Data API v3 key")
    parser.add_argument("--input",   default=INPUT_CSV,   help=f"Input CSV (default: {INPUT_CSV})")
    parser.add_argument("--output",  default=OUTPUT_JSON, help=f"Output JSON (default: {OUTPUT_JSON})")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if not r["Title"].startswith("[Deleted")]

    ids = [r["ID"] for r in rows]
    batches = [ids[i : i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
    print(f"{len(ids)} videos · {len(batches)} API batches\n")

    meta = {}
    for i, batch in enumerate(batches, 1):
        data = fetch_batch(batch, args.api_key)
        for item in data.get("items", []):
            snip = item["snippet"]
            meta[item["id"]] = {
                "channel":   snip.get("channelTitle", ""),
                "published": snip.get("publishedAt", "")[:10],
                "duration":  parse_duration(item.get("contentDetails", {}).get("duration", "")),
                "tags":      snip.get("tags", []),
            }
        print(f"  Batch {i}/{len(batches)} — {len(data.get('items', []))} items")
        time.sleep(SLEEP_SEC)

    result = []
    for r in rows:
        vid_id = r["ID"]
        m = meta.get(vid_id, {})
        result.append({
            "id":        vid_id,
            "title":     r["Title"],
            "channel":   m.get("channel", ""),
            "published": m.get("published", ""),
            "duration":  m.get("duration", ""),
            "tags":      m.get("tags", []),
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(result)} videos saved to '{args.output}'")


if __name__ == "__main__":
    main()
