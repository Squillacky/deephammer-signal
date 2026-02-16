"""
DeepHammer Phase 2B - Deepgram Nova-2 Transcription
"""

import os
import json
import time
import httpx
from pathlib import Path
from deephammer.config import config

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"
PARAMS = {
    "model": "nova-2",
    "smart_format": "true",
    "paragraphs": "true",
    "utterances": "true",
    "diarize": "true",
    "language": "en",
}

def load_report():
    report_path = os.path.join(config.METADATA_DIR, "outlier_report.json")
    with open(report_path, "r") as f:
        return json.load(f)

def transcribe_file(audio_path):
    headers = {
        "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/mpeg",
    }
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    timeout = max(120, int(file_size_mb * 15))
    response = httpx.post(
        DEEPGRAM_URL,
        params=PARAMS,
        headers=headers,
        content=audio_data,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()

def extract_transcript(dg_response):
    results = dg_response.get("results", {})
    channels = results.get("channels", [{}])
    alternatives = channels[0].get("alternatives", [{}]) if channels else [{}]
    alt = alternatives[0] if alternatives else {}
    transcript_text = alt.get("transcript", "")
    paragraphs_data = alt.get("paragraphs", {})
    paragraphs = []
    if paragraphs_data and "paragraphs" in paragraphs_data:
        for p in paragraphs_data["paragraphs"]:
            paragraphs.append({
                "start": p.get("start", 0),
                "end": p.get("end", 0),
                "speaker": p.get("speaker", 0),
                "text": " ".join(s.get("text", "") for s in p.get("sentences", [])),
            })
    words = alt.get("words", [])
    word_count = len(words)
    metadata = dg_response.get("metadata", {})
    duration = metadata.get("duration", 0)
    speakers = set()
    for w in words:
        if "speaker" in w:
            speakers.add(w["speaker"])
    return {
        "transcript": transcript_text,
        "paragraphs": paragraphs,
        "word_count": word_count,
        "duration_seconds": round(duration, 2),
        "speaker_count": len(speakers) if speakers else 1,
        "confidence": round(alt.get("confidence", 0), 4),
    }

def run():
    report = load_report()
    audio_dir = os.path.join(config.DATA_DIR, "audio")
    transcripts_dir = config.TRANSCRIPTS_DIR
    os.makedirs(transcripts_dir, exist_ok=True)
    transcription_queue = []
    for video in report.get("outliers", []):
        vid = video.get("id", "")
        audio_path = os.path.join(audio_dir, f"{vid}.mp3")
        transcript_path = os.path.join(transcripts_dir, f"{vid}.json")
        if os.path.exists(audio_path) and not os.path.exists(transcript_path):
            transcription_queue.append((video, audio_path, transcript_path))
    if not transcription_queue:
        already = sum(1 for v in report.get("outliers", [])
                      if os.path.exists(os.path.join(transcripts_dir, f"{v.get('id','')}.json")))
        print(f"\n  No new files to transcribe. ({already} already complete)")
        return
    print(f"\n--- Deepgram Nova-2 Transcription ---")
    print(f"  Queue: {len(transcription_queue)} files\n")
    total_cost = 0
    for i, (video, audio_path, transcript_path) in enumerate(transcription_queue, 1):
        vid = video.get("id", "")
        title = video.get("title", "Unknown")[:50]
        file_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"  [{i}/{len(transcription_queue)}] {vid} - {title}...")
        start_time = time.time()
        try:
            dg_response = transcribe_file(audio_path)
            result = extract_transcript(dg_response)
            elapsed = time.time() - start_time
            duration_min = result["duration_seconds"] / 60
            cost = duration_min * 0.0043
            total_cost += cost
            output = {
                "video_id": vid,
                "title": video.get("title", ""),
                "views": video.get("views", 0),
                "sigma": video.get("sigma", 0),
                **result,
            }
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"         {result['word_count']:,} words | {result['speaker_count']} speaker(s) | conf: {result['confidence']:.3f} | {elapsed:.1f}s")
        except Exception as e:
            print(f"         ERROR: {e}")
            continue
        if i < len(transcription_queue):
            time.sleep(1)
    completed = sum(1 for v in report.get("outliers", [])
                    if os.path.exists(os.path.join(transcripts_dir, f"{v.get('id','')}.json")))
    print(f"\n--- Transcription Summary ---")
    print(f"  Completed: {completed}/{len(transcription_queue)}")
    print(f"  Estimated cost: {total_cost:.4f}")
    print(f"  Transcripts: {transcripts_dir}")

if __name__ == "__main__":
    run()




