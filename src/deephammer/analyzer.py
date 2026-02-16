"""Phase 3 – Claude Sonnet 4 content analysis for SIGNAL."""

import json
import time
from pathlib import Path
from anthropic import Anthropic
from deephammer.config import config

MODEL = "claude-sonnet-4-20250514"
TRANSCRIPT_DIR = Path(config.DATA_DIR) / "transcripts"
ANALYSIS_DIR = Path(config.DATA_DIR) / "analysis"
OUTLIER_REPORT = Path(config.DATA_DIR) / "outlier_report.json"

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are an expert YouTube content analyst specializing in viral video mechanics. 
Analyze the provided transcript and return ONLY valid JSON with this exact structure:

{
  "hook_anatomy": {
    "first_5_seconds": "exact opening words",
    "hook_type": "curiosity_gap|pattern_interrupt|bold_claim|story_open|direct_challenge",
    "hook_strength": 1-10,
    "emotional_trigger": "string"
  },
  "narrative_structure": {
    "framework": "problem_solution|story_arc|list_format|investigation|tutorial",
    "act_breakdown": [{"act": 1, "description": "string", "timestamp_approx": "string"}],
    "tension_peaks": ["string"],
    "payoff_delivery": "string"
  },
  "rhetorical_devices": [
    {"device": "string", "example": "exact quote", "frequency": "high|medium|low"}
  ],
  "virality_factors": {
    "shareability_score": 1-10,
    "controversy_level": 1-10,
    "information_density": 1-10,
    "emotional_arc": "string",
    "target_audience": "string",
    "click_triggers": ["string"]
  },
  "content_patterns": {
    "primary_topic": "string",
    "secondary_topics": ["string"],
    "expertise_signals": ["string"],
    "unique_angle": "string"
  },
  "key_quotes": ["string"],
  "one_line_summary": "string"
}"""

def load_view_counts() -> dict:
    """Pull real view counts from outlier report."""
    if OUTLIER_REPORT.exists():
        with open(OUTLIER_REPORT) as f:
            report = json.load(f)
        return {v["id"]: v.get("views", 0) for v in report.get("outliers", [])}
    return {}

def analyze_transcript(video_id: str, transcript_data: dict, view_counts: dict) -> dict:
    """Send transcript to Claude Sonnet 4 for analysis."""
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    views = view_counts.get(video_id, transcript_data.get("views", 0))
    title = transcript_data.get("title", "Unknown")
    transcript = transcript_data.get("transcript", "")
    word_count = transcript_data.get("word_count", 0)
    
    user_message = f"""Analyze this YouTube video transcript:

TITLE: {title}
VIEWS: {views:,}
WORD COUNT: {word_count}
VIDEO ID: {video_id}

TRANSCRIPT:
{transcript}"""

    print(f"    Sending to {MODEL} ({word_count:,} words)...")
    start = time.time()
    
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    elapsed = time.time() - start
    raw = response.content[0].text
    
    # Parse JSON from response
    try:
        # Handle potential markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        analysis = {"raw_response": raw, "parse_error": True}
    
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    
    print(f"    Done in {elapsed:.1f}s | {tokens_in:,} in / {tokens_out:,} out")
    
    return {
        "video_id": video_id,
        "title": title,
        "views": views,
        "model": MODEL,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "elapsed_seconds": round(elapsed, 1),
        "analysis": analysis
    }

def main():
    print("=" * 60)
    print("PHASE 3: CONTENT ANALYSIS via Claude Sonnet 4")
    print("=" * 60)
    
    view_counts = load_view_counts()
    transcripts = sorted(TRANSCRIPT_DIR.glob("*.json"))
    
    print(f"Found {len(transcripts)} transcripts")
    print(f"View counts loaded: {len(view_counts)} videos")
    print(f"Model: {MODEL}")
    print("-" * 60)
    
    total_in = 0
    total_out = 0
    results = []
    
    for i, path in enumerate(transcripts, 1):
        video_id = path.stem
        print(f"\n[{i}/{len(transcripts)}] {video_id}")
        
        with open(path) as f:
            data = json.load(f)
        
        print(f"    Title: {data.get('title', 'Unknown')[:55]}...")
        
        try:
            result = analyze_transcript(video_id, data, view_counts)
            results.append(result)
            total_in += result["tokens_in"]
            total_out += result["tokens_out"]
            
            # Save individual analysis
            out_path = ANALYSIS_DIR / f"{video_id}.json"
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"    Saved: {out_path.name}")
            
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"video_id": video_id, "error": str(e)})
    
    # Summary
    cost_in = (total_in / 1_000_000) * 3.0   # Sonnet 4 input price
    cost_out = (total_out / 1_000_000) * 15.0  # Sonnet 4 output price
    
    print("\n" + "=" * 60)
    print("PHASE 3 COMPLETE")
    print(f"  Analyzed: {len([r for r in results if 'error' not in r])}/{len(transcripts)}")
    print(f"  Total tokens: {total_in:,} in / {total_out:,} out")
    print(f"  Estimated cost: ${cost_in + cost_out:.3f}")
    print(f"  Output: {ANALYSIS_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
