# 🔨 DeepHammer SIGNAL

**Structured Influencer Generation, Navigation, Analysis & Learning**

> Reverse-engineer what makes a creator's best content work — for $0.74.

---

## What This Is

DeepHammer SIGNAL is an AI-powered content intelligence pipeline. Point it at any YouTube channel, and it will:

1. **Catalog** every video with full metadata (titles, views, dates, durations)
2. **Detect** statistical outliers — the videos that broke the algorithm
3. **Transcribe** top performers using Deepgram Nova-2
4. **Analyze** content patterns using Anthropic Claude
5. **Synthesize** a creator blueprint — hook formulas, narrative structures, audience triggers

This first implementation targets **Nate B. Jones** ([@NateBJones](https://www.youtube.com/@NateBJones)) — 459 videos, 9M+ total views.

---

## Key Findings

| Metric | Value |
|---|---|
| Videos cataloged | 459 |
| Total channel views | 9,008,391 |
| Outlier threshold (2.0σ) | 92,058 views |
| Outliers identified | 17 |
| Top 5 transcribed & analyzed | ✓ |
| **Total pipeline cost** | **$0.74** |

**Creator Archetype:** Tech industry financial detective
**Hook Formula:** Massive dollar figure → contradictory claim → insider revelation
**Narrative Engine:** 80% investigation framework, 6-beat story pattern
**Ideal Length:** 18–25 minutes

> Full findings: [`data/signal_report.json`](data/signal_report.json)

---

## Architecture

YouTube Channel │ ▼ ┌─────────────┐ yt-dlp (metadata only) │ Phase 1 │──→ channel_catalog.json (459 videos) │ Scanner │ └─────────────┘ │ ▼ ┌─────────────┐ Statistical outlier detection (σ configurable) │ Phase 2 │──→ outlier_report.json (17 outliers @ 2.0σ) │ Outliers │ └─────────────┘ │ ▼ ┌─────────────┐ Deepgram Nova-2 ($0.55) │ Phase 3a │──→ transcripts/.json (top 5) │ Transcribe │ └─────────────┘ │ ▼ ┌─────────────┐ Anthropic Claude ($0.16) │ Phase 3b │──→ analysis/.json (top 5) │ Analyze │ └─────────────┘ │ ▼ ┌─────────────┐ Anthropic Claude ($0.03) │ Phase 4 │──→ signal_report.json │ Synthesize │ └─────────────┘




---

## Project Structure

deephammer-signal/ ├── main.py # Pipeline orchestrator (Phases 1-3) ├── synthesize.py # Synthesis orchestrator (Phase 4) ├── pyproject.toml # Dependencies and project metadata ├── src/deephammer/ │ ├── config.py # Environment and API key loader │ ├── scanner.py # YouTube channel cataloger via yt-dlp │ ├── outliers.py # Statistical outlier detection engine │ ├── transcriber.py # Deepgram Nova-2 transcription │ ├── analyzer.py # Claude content analysis │ └── repair_json.py # LLM output sanitizer └── data/ ├── signal_report.json # Final synthesis (Phase 4 output) ├── metadata/ │ ├── channel_catalog.json │ └── outlier_report.json ├── transcripts/ # Deepgram outputs (top 5) └── analysis/ # Claude outputs (top 5)




---

## Installation

```bash
git clone https://github.com/Squillacky/deephammer-signal.git
cd deephammer-signal
uv sync
Environment Variables
Create a .env file in the project root:



DEEPGRAM_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
Usage
bash


# Run the full pipeline (Phases 1-3)
uv run python main.py

# Generate the synthesis report (Phase 4)
uv run python synthesize.py
Cost Breakdown


Phase	Service	Cost
1 — Catalog	yt-dlp (local)	$0.00
2 — Outliers	Python (local)	$0.00
3a — Transcription	Deepgram Nova-2	$0.55
3b — Analysis	Anthropic Claude	$0.16
4 — Synthesis	Anthropic Claude	$0.03
Total		$0.74
What's Next
 CLI interface (deephammer analyze <channel_url>)
 Multi-channel comparative analysis
 Automated content generation from blueprints
 Cost optimization benchmarks across LLM providers
License
MIT

Author
Scott A. Squillace — The Cyber CFO

Building AI-powered financial intelligence tools. This project demonstrates that meaningful content analysis doesn't require enterprise budgets — it requires the right architecture.





