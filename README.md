# watchlater-migrator

A toolkit to rescue, triage, and migrate your YouTube **Watch Later** playlist when it has grown out of control.

YouTube's Watch Later is a black box: no bulk export, no filtering, no easy cleanup. This project gives you the tools to take back control.

---

## How it works

```
Step 1 — Export       →  Step 2 — Enrich       →  Step 3 — Triage       →  Step 4 — Import
1_export_watchlater.py   2_enrich_metadata.py      3_triage.html            4_import_to_youtube.py
(yt-dlp + cookies)       (YouTube Data API v3)      (local HTML tool)        (OAuth2 + API)

watch_later_public.csv → enriched.json          → keepers.json           → YouTube playlist ✓
```

---

## Why not use the YouTube API to read Watch Later?

The YouTube Data API v3 explicitly blocks access to the Watch Later playlist (`WL`), even with OAuth authentication. The only reliable way to read it is via **yt-dlp** using your browser's cookies — which is what step 1 does.

Writing to regular playlists, however, works fine via the API (step 4).

---

## Prerequisites

- Python 3.10+
- Firefox or Chrome, logged into YouTube
- A Google Cloud project with **YouTube Data API v3** enabled

---

## Setup

```bash
git clone https://github.com/jbijjer/watchlater-migrator.git
cd watchlater-migrator
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 1 — Export Watch Later

```bash
python3 1_export_watchlater.py
```

Edit the `BROWSER` variable at the top of the script (`"firefox"` or `"chrome"`).

> **Note:** Close your browser completely before running. yt-dlp reads the cookie database directly from disk.

**Output:**
- `watch_later_public.csv` — public videos (ID, title)
- `watch_later_private.csv` — private/deleted videos

---

## Step 2 — Enrich metadata

Get a free YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com) ([official guide](https://developers.google.com/youtube/v3/getting-started)):
1. Create a project → **APIs & Services** → **Library** → enable **YouTube Data API v3**
2. **Credentials** → **Create Credentials** → **API Key**

```bash
python3 2_enrich_metadata.py --api-key YOUR_API_KEY
```

> The free tier allows 10,000 units/day. Fetching metadata for 1,000 videos costs ~20 units (batches of 50).

**Output:** `enriched.json` — all videos with channel, publish date, duration, and tags.

> ⚠️ **Rotate your API key after use** — never commit it to git.

---

## Step 3 — Triage

Open `3_triage.html` in your browser (no server needed — it runs fully offline).

Drag and drop your `enriched.json` file onto the page.

**Features:**
- Filter by channel, year, or keyword search
- Sort by any column (title, channel, year, duration, status)
- Multi-select with Shift+click and Ctrl+click
- Mark videos as **To Keep** or **Deleted**
- Toggle visibility of kept/deleted videos
- Reset all statuses via the ⋯ menu
- Export `keepers.json` when done

---

## Step 4 — Import keepers to YouTube

You need an **OAuth 2.0 client** (not just an API key) to write to YouTube playlists.

1. In Google Cloud Console → **APIs & Services** → **Credentials**
2. Configure the **OAuth consent screen** (External, add your Gmail as test user)
3. **Create Credentials** → **OAuth 2.0 Client ID** → **Desktop app**
4. Download the JSON and rename it to `client_secrets.json`

```bash
python3 4_import_to_youtube.py
```

A browser window will open for Google authentication. The script then creates a private playlist named **"old WatchLater"** and adds all your keepers.

**Options:**
```bash
python3 4_import_to_youtube.py --playlist "My Saved Videos" --keepers my_keepers.json
```

---

## Step 5 — Clear Watch Later

YouTube has no native "clear all" button. Use the **[YouTube Watch Later Bulk Delete](https://chromewebstore.google.com/detail/youtube-watch-later-bulk/lhpdoldlalakkdipneepcpomkofkbca)** Chrome extension. It removes all videos automatically — about 1 second per video.

---

## File structure

```
watchlater-migrator/
├── 1_export_watchlater.py      # Export Watch Later via yt-dlp
├── 2_enrich_metadata.py        # Fetch metadata via YouTube API
├── 3_triage.html               # Local triage tool (no server needed)
├── 4_import_to_youtube.py      # Create playlist + import keepers
├── requirements.txt
├── .gitignore
└── README.md
```

---

## requirements.txt

```
yt-dlp
tqdm
requests
google-auth-oauthlib
google-api-python-client
secretstorage
```

---

## Security notes

- Never commit `client_secrets.json` or your API key to git (both are in `.gitignore`)
- Your browser cookies are read locally by yt-dlp and never transmitted anywhere
- The OAuth flow runs locally on your machine

---

## License

MIT
