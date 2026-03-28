"""
Step 4 — Import keepers into a new private YouTube playlist.

Creates a new private playlist named "old WatchLater" (or a custom name)
and adds all videos from your keepers.json file.

Requirements:
    pip install google-auth-oauthlib google-api-python-client

Usage:
    python3 4_import_to_youtube.py
    python3 4_import_to_youtube.py --playlist "My Saved Videos" --keepers my_keepers.json

Output:
    A new private YouTube playlist with all your keeper videos.
"""

import json
import time
import argparse
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# ── Configuration ────────────────────────────────────────────────────────────

SCOPES          = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS  = "client_secrets.json"
KEEPERS_FILE    = "keepers.json"
PLAYLIST_NAME   = "old WatchLater"
SLEEP_SEC       = 0.3   # between insertions to avoid rate limiting


# ── Helpers ──────────────────────────────────────────────────────────────────

def authenticate(secrets_path: str):
    flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)


def create_playlist(youtube, name: str) -> str:
    resp = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": name,
                "description": "Migrated from YouTube Watch Later via watchlater-migrator.",
            },
            "status": {"privacyStatus": "private"},
        },
    ).execute()
    playlist_id = resp["id"]
    print(f'✅ Playlist created: "{name}"')
    print(f"   https://www.youtube.com/playlist?list={playlist_id}\n")
    return playlist_id


def add_video(youtube, playlist_id: str, video_id: str):
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        },
    ).execute()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import keepers into a YouTube playlist.")
    parser.add_argument("--keepers",  default=KEEPERS_FILE,   help=f"Keepers JSON file (default: {KEEPERS_FILE})")
    parser.add_argument("--playlist", default=PLAYLIST_NAME,  help=f'Playlist name (default: "{PLAYLIST_NAME}")')
    parser.add_argument("--secrets",  default=CLIENT_SECRETS, help=f"OAuth secrets file (default: {CLIENT_SECRETS})")
    args = parser.parse_args()

    if not Path(args.secrets).exists():
        print(f"❌ {args.secrets} not found.")
        print("Download it from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID → Download JSON")
        return

    keepers = json.loads(Path(args.keepers).read_text(encoding="utf-8"))
    print(f"{len(keepers)} videos to import\n")

    print("Opening browser for Google authentication...")
    youtube = authenticate(args.secrets)
    print("Authenticated!\n")

    playlist_id = create_playlist(youtube, args.playlist)

    errors = []
    for i, video in enumerate(keepers, 1):
        vid_id = video["id"]
        title  = video.get("title", vid_id)
        try:
            add_video(youtube, playlist_id, vid_id)
            print(f"  [{i:02d}/{len(keepers)}] ✓ {title[:70]}")
            time.sleep(SLEEP_SEC)
        except HttpError as e:
            print(f"  [{i:02d}/{len(keepers)}] ✗ {title[:60]} → {e}")
            errors.append({"id": vid_id, "title": title, "error": str(e)})

    print(f"\n── Summary ──────────────────────────────")
    print(f"✓ {len(keepers) - len(errors)} videos added")
    if errors:
        print(f"✗ {len(errors)} errors:")
        for e in errors:
            print(f"  - {e['title'][:60]}: {e['error']}")
    print(f"\nPlaylist: https://www.youtube.com/playlist?list={playlist_id}")


if __name__ == "__main__":
    main()
