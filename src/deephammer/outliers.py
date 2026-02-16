import json
import statistics
import subprocess
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.deephammer.config import config

METADATA_DIR = Path(config.METADATA_DIR)
AUDIO_DIR = Path(config.DATA_DIR) / "audio"
SIGMA_THRESHOLD = 2.0
WINDOW_DAYS = 14

def load_catalog():
    catalog_path = METADATA_DIR / "channel_catalog.json"
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_outliers(catalog):
    videos = catalog["videos"]
    views = [v["view_count"] for v in videos if v.get("view_count")]
    mean = statistics.mean(views)
    stdev = statistics.stdev(views)
    threshold = mean + (SIGMA_THRESHOLD * stdev)

    print(f"--- Outlier Detection ---")
    print(f"  Videos with view data: {len(views)}")
    print(f"  Mean views: {mean:,.0f}")
    print(f"  Std dev: {stdev:,.0f}")
    print(f"  Threshold ({SIGMA_THRESHOLD}s): {threshold:,.0f}\n")

    outliers = [
        v for v in videos
        if v.get("view_count") and v["view_count"] >= threshold
    ]
    outliers.sort(key=lambda v: v["view_count"], reverse=True)

    print(f"  Outliers found: {len(outliers)}\n")
    for i, v in enumerate(outliers, 1):
        sigma = (v["view_count"] - mean) / stdev
        print(f"    {i:>2}. {v['view_count']:>10,} ({sigma:.1f}s) | {v['title'][:55]}")

    return outliers, {"mean": mean, "stdev": stdev, "threshold": threshold}

def filter_by_window(outliers):
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    cutoff_str = cutoff.strftime("%Y%m%d")

    recent = [v for v in outliers if (v.get("upload_date") or "00000000") >= cutoff_str]
    older = [v for v in outliers if (v.get("upload_date") or "00000000") < cutoff_str]

    print(f"\n--- Window Filter ({WINDOW_DAYS} days) ---")
    print(f"  Recent (will transcribe): {len(recent)}")
    print(f"  Older (metadata only): {len(older)}")

    if recent:
        print(f"\n  Queue:")
        for v in recent:
            dur = int(v.get("duration") or 0)
            print(f"    {v['id']} | {dur//60}m{dur%60:02d}s | {v['title'][:50]}")

    return recent

def download_audio(video):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_path = AUDIO_DIR / f"{video['id']}.mp3"

    if output_path.exists():
        print(f"  [cached] {video['id']}")
        return output_path

    print(f"  [download] {video['id']} - {video['title'][:40]}...")

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "-o", str(output_path),
        "--no-playlist",
        "--no-warnings",
        video["url"]
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  [FAILED] {result.stderr[:200]}")
        return None

    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  [done] {size_mb:.1f} MB")
        return output_path
    else:
        print(f"  [FAILED] File not created")
        return None

def run():
    catalog = load_catalog()
    outliers, stats = find_outliers(catalog)

    if not outliers:
        print("\nNo outliers found.")
        return

    queue = filter_by_window(outliers)

    if not queue:
        print("\nNo recent outliers to transcribe.")
        print("Expanding to top 5 all-time outliers for initial analysis...")
        queue = outliers[:5]
        print(f"\n  Expanded queue:")
        for v in queue:
            dur = int(v.get("duration") or 0)
            print(f"    {v['id']} | {dur//60}m{dur%60:02d}s | {v['title'][:50]}")

    print(f"\n--- Downloading Audio ---")
    downloaded = []
    for v in queue:
        path = download_audio(v)
        if path:
            downloaded.append({"video": v, "audio_path": str(path)})

    report_path = METADATA_DIR / "outlier_report.json"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "sigma_threshold": SIGMA_THRESHOLD,
        "total_outliers": len(outliers),
        "queue_size": len(queue),
        "downloaded": len(downloaded),
        "outliers": outliers,
        "queue": [d["video"] for d in downloaded]
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n--- Phase 2 Summary ---")
    print(f"  Outliers identified: {len(outliers)}")
    print(f"  Audio downloaded: {len(downloaded)}")
    print(f"  Report saved: {report_path}")

if __name__ == "__main__":
    run()


