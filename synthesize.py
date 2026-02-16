"""PROJECT SIGNAL - Phase 4: Synthesis Engine"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata" / "outlier_report.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "signal_report.json"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8000


def load_analyses():
    report = json.load(open(METADATA_PATH))
    meta_map = {}
    for item in report["outliers"]:
        meta_map[item["id"]] = {"title": item["title"], "view_count": item["view_count"], "duration": item.get("duration", 0), "upload_date": item.get("upload_date", "")}
    analyses = []
    for path in sorted(ANALYSIS_DIR.glob("*.json")):
        video_id = path.stem
        data = json.load(open(path))
        meta = meta_map.get(video_id, {})
        analyses.append({"video_id": video_id, "title": meta.get("title", "Unknown"), "view_count": meta.get("view_count", 0), "duration": meta.get("duration", 0), "upload_date": meta.get("upload_date", ""), "analysis": data["analysis"]})
    analyses.sort(key=lambda x: x["view_count"], reverse=True)
    return analyses


def build_prompt(analyses):
    analyses_text = json.dumps(analyses, indent=2)
    system = "You are a world-class content strategist and audience intelligence analyst. You specialize in reverse-engineering why certain videos massively outperform others on a creator's channel. You think in systems, not opinions. Every claim must trace back to evidence in the data provided."
    prompt = f"""Below are detailed content analyses of the top-performing outlier videos from a single YouTube creator's channel (459 total videos, 9M+ total views). These {len(analyses)} videos represent the statistical outliers.

ANALYSES:
{analyses_text}

YOUR TASK: Synthesize these individual analyses into a single CREATOR BLUEPRINT.

Respond with a JSON object using this exact structure:
{{
  "creator_blueprint": {{
    "creator_identity": {{
      "archetype": "one phrase describing what role this creator plays",
      "core_value_proposition": "what the audience gets that they cannot get elsewhere",
      "authority_signals": ["list of techniques used to establish credibility"]
    }},
    "hook_formula": {{
      "pattern": "describe the repeatable hook structure across all outliers",
      "elements": ["list the specific elements present in high-performing hooks"],
      "avg_strength": 0,
      "opening_word_count_sweet_spot": "range estimate"
    }},
    "narrative_engine": {{
      "dominant_framework": "the primary storytelling structure",
      "framework_distribution": {{}},
      "structural_beats": ["ordered list of narrative beats that repeat"],
      "tension_mechanics": "how the creator builds and sustains tension"
    }},
    "virality_mechanics": {{
      "shareability_drivers": ["what makes people share these videos"],
      "information_density_strategy": "how creator packs value without losing clarity",
      "avg_shareability": 0,
      "avg_information_density": 0,
      "audience_trigger": "the core emotional/intellectual trigger"
    }},
    "content_dna": {{
      "topic_selection_pattern": "what kinds of topics get chosen and why",
      "research_depth_signal": "how creator signals deep research",
      "differentiator": "what separates this creator from others",
      "content_moat": "structural advantage hard to copy"
    }},
    "replication_playbook": {{
      "title_formula": "reverse-engineered title pattern with template",
      "thumbnail_implications": "what content suggests about visual strategy",
      "ideal_video_length": "recommended length range based on data",
      "topic_criteria": ["checklist for evaluating topic fit"],
      "production_notes": ["tactical notes on pacing, editing, delivery"]
    }},
    "strategic_recommendations": ["ranked list of 5 specific actionable recommendations"]
  }},
  "meta": {{
    "videos_analyzed": 0,
    "total_outlier_views": 0,
    "channel_total_views": 9008391,
    "outlier_share_of_views": "percentage",
    "synthesis_confidence": "high/medium/low with justification"
  }}
}}

IMPORTANT: Ground every insight in evidence from the analyses. Do not invent data. The replication_playbook should be concrete enough that a producer could execute against it. Return ONLY the JSON object."""
    return system, prompt


def run_synthesis(analyses):
    client = anthropic.Anthropic()
    system, prompt = build_prompt(analyses)
    print(f"  Sending {len(analyses)} analyses to {MODEL}...")
    print(f"  Prompt size: ~{len(prompt):,} chars")
    print()
    response = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=system, messages=[{"role": "user", "content": prompt}])
    raw = response.content[0].text
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens, "total_tokens": response.usage.input_tokens + response.usage.output_tokens, "model": MODEL, "cost_estimate": round((response.usage.input_tokens * 0.003 + response.usage.output_tokens * 0.015) / 1000, 4)}
    return raw, usage


def parse_response(raw):
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  WARNING: JSON parse failed: {e}")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        raw_path = PROJECT_ROOT / "data" / "signal_report_raw.txt"
        raw_path.write_text(raw, encoding="utf-8")
        print(f"  Raw response saved to {raw_path}")
        sys.exit(1)


def main():
    print()
    print("=" * 70)
    print("  PROJECT SIGNAL - Phase 4: Synthesis Engine")
    print("=" * 70)
    print()
    print("[1/4] Loading analyses...")
    analyses = load_analyses()
    print(f"  Found {len(analyses)} video analyses")
    for a in analyses:
        print(f"    {a['video_id']}  |  {a['view_count']:>9,} views  |  {a['title'][:50]}")
    print()
    print("[2/4] Running synthesis via Claude...")
    raw, usage = run_synthesis(analyses)
    print(f"  Tokens: {usage['total_tokens']:,} (in: {usage['input_tokens']:,}, out: {usage['output_tokens']:,})")
    print(f"  Cost:   ${usage['cost_estimate']}")
    print()
    print("[3/4] Parsing response...")
    blueprint = parse_response(raw)
    print("  Parsed creator blueprint successfully")
    print()
    print("[4/4] Saving report...")
    output = {"generated_at": datetime.now(timezone.utc).isoformat(), "phase": "4_synthesis", "source_videos": len(analyses), "usage": usage}
    output.update(blueprint)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved: {OUTPUT_PATH}")
    print(f"  Size:  {OUTPUT_PATH.stat().st_size:,} bytes")
    print()
    bp = blueprint.get("creator_blueprint", {})
    meta = blueprint.get("meta", {})
    ci = bp.get("creator_identity", {})
    ne = bp.get("narrative_engine", {})
    vm = bp.get("virality_mechanics", {})
    print("=" * 70)
    print("  SYNTHESIS COMPLETE")
    print("=" * 70)
    print(f"  Archetype:          {ci.get('archetype', '?')}")
    print(f"  Value Prop:         {ci.get('core_value_proposition', '?')[:70]}")
    print(f"  Dominant Framework: {ne.get('dominant_framework', '?')}")
    print(f"  Audience Trigger:   {vm.get('audience_trigger', '?')}")
    print(f"  Confidence:         {meta.get('synthesis_confidence', '?')}")
    print()
    for i, rec in enumerate(bp.get("strategic_recommendations", []), 1):
        print(f"    {i}. {rec[:85]}")
    print()
    print(f"  Phase 4 cost: ${usage['cost_estimate']}")
    print()


if __name__ == "__main__":
    main()