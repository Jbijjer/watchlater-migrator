"""
Step 1 — Export your YouTube Watch Later playlist to CSV.

Uses yt-dlp with your browser cookies to access the Watch Later playlist,
which is not accessible via the YouTube Data API.

Requirements:
    pip install yt-dlp tqdm

Usage:
    python3 1_export_watchlater.py

Output:
    watch_later_public.csv   — public videos (id, title)
    watch_later_private.csv  — private/deleted videos
"""

import os
import sys
import csv
from typing import Optional, Tuple, List

import yt_dlp
from tqdm import tqdm


# ── Configuration ────────────────────────────────────────────────────────────

BROWSER = "firefox"          # "firefox" or "chrome"
PROFILE_PATH = None          # Optional: path to a non-default browser profile
OUTPUT_PUBLIC  = "watch_later_public.csv"
OUTPUT_PRIVATE = "watch_later_private.csv"
PLAYLIST_URL   = "https://www.youtube.com/playlist?list=WL"


# ── Helpers ──────────────────────────────────────────────────────────────────

class _QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(msg, file=sys.stderr)


def _fetch_flat(browser: str, profile_path: Optional[str]):
    cookies_arg = (browser, profile_path) if profile_path else (browser,)
    opts = {
        "cookiesfrombrowser": cookies_arg,
        "quiet": True,
        "logger": _QuietLogger(),
        "extract_flat": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(PLAYLIST_URL, download=False)

    if not (info and info.get("entries")):
        raise RuntimeError("Could not retrieve Watch Later playlist.")

    public, private = [], []
    for entry in info["entries"]:
        if not entry:
            continue
        if entry.get("title") == "[Private video]":
            private.append(entry)
        else:
            public.append(entry)
    return public, private


def _write_csv(path: str, videos: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Title"])
        for v in tqdm(videos, unit=" video"):
            writer.writerow([v.get("id", "N/A"), v.get("title", "N/A")])


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    supported = ["firefox", "chrome"]
    if BROWSER not in supported:
        print(f"ERROR: BROWSER must be one of {supported}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching Watch Later using {BROWSER.capitalize()} cookies...")
    if PROFILE_PATH:
        print(f"Profile: {PROFILE_PATH}")

    try:
        public, private = _fetch_flat(BROWSER, PROFILE_PATH)
    except yt_dlp.utils.DownloadError as e:
        print(f"\n❌ yt-dlp error: {e}", file=sys.stderr)
        print("Make sure your browser is closed and you are logged into YouTube.", file=sys.stderr)
        sys.exit(1)

    public.reverse()
    private.reverse()

    print(f"\nFound {len(public)} public videos and {len(private)} private/deleted videos.")

    if public:
        print(f"\nWriting public videos to '{OUTPUT_PUBLIC}'...")
        _write_csv(OUTPUT_PUBLIC, public)

    if private:
        print(f"Writing private videos to '{OUTPUT_PRIVATE}'...")
        _write_csv(OUTPUT_PRIVATE, private)

    print("\n✅ Export complete.")


if __name__ == "__main__":
    main()
