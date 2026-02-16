import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.deephammer.config import config

CHANNEL_URL = config.YOUTUBE_CHANNEL_URL
METADATA_DIR = Path(config.METADATA_DIR)

def scan_channel():
    print(f"Scanning {CHANNEL_URL} ...")
    print("This will take a few minutes for 700+ videos.\n")

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-download",
        "--no-warnings",
        f"{CHANNEL_URL}/videos"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"yt-dlp error: {result.stderr[:500]}")
        return

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            videos.append({
                "id": entry.get("id"),
                "title": entry.get("title"),
                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                "duration": entry.get("duration"),
                "view_count": entry.get("view_count"),
                "upload_date": entry.get("upload_date"),
                "description": entry.get("description", ""),
            })
        except json.JSONDecodeError:
            continue

    print(f"Found {len(videos)} videos\n")

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    catalog_path = METADATA_DIR / "channel_catalog.json"
    catalog = {
        "channel": CHANNEL_URL,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "video_count": len(videos),
        "videos": videos
    }

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Catalog saved: {catalog_path}")
    print(f"File size: {catalog_path.stat().st_size / 1024:.1f} KB\n")

    if videos:
        dates = [v["upload_date"] for v in videos if v.get("upload_date")]
        views = [v["view_count"] for v in videos if v.get("view_count")]
        print("--- Channel Summary ---")
        print(f"  Videos: {len(videos)}")
        if dates:
            print(f"  Oldest: {min(dates)}")
            print(f"  Newest: {max(dates)}")
        if views:
            print(f"  Total views: {sum(views):,}")
            print(f"  Avg views: {sum(views)//len(views):,}")
            top = sorted(videos, key=lambda v: v.get("view_count", 0), reverse=True)[:5]
            print(f"\n  Top 5 by views:")
            for i, v in enumerate(top, 1):
                print(f"    {i}. {v['view_count']:>10,} | {v['title'][:60]}")

if __name__ == "__main__":
    scan_channel()
