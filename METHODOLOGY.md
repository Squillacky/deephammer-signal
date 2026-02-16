code METHODOLOGY.md

# Methodology

## Research Question

> Given only a creator's public YouTube channel URL, can we algorithmically identify their highest-performing content patterns and reverse-engineer a reusable "creator blueprint" — for under $1.00?

---

## Approach

SIGNAL uses a four-phase pipeline that mirrors how a forensic financial analyst would audit a business: catalog everything, find the anomalies, investigate the outliers, and synthesize findings.

### Phase 1 — Cataloging

- **Tool:** yt-dlp (metadata-only extraction, no video downloads)
- **Method:** Extract title, view count, upload date, duration, and tags for every public video on the target channel
- **Output:** `channel_catalog.json` — a complete inventory of 459 videos

No API key required. No rate limiting encountered. Total cost: **$0.00**.

### Phase 2 — Outlier Detection

- **Tool:** Custom Python (NumPy)
- **Method:** Calculate mean and standard deviation of view counts across the full catalog. Flag any video exceeding the mean + 2.0σ as a statistical outlier
- **Threshold:** 92,058 views (mean 19,626 + 2.0 × 36,216)
- **Output:** `outlier_report.json` — 17 videos flagged from 459 (3.7% of catalog)

The 2.0σ threshold was chosen to balance signal density against sample size. A 3.0σ threshold returned only 4 videos — too few for pattern extraction. 1.5σ returned 31 — too noisy.

Total cost: **$0.00**.

### Phase 3 — Transcription & Content Analysis

- **Tool:** Deepgram Nova-2 (speech-to-text), Anthropic Claude 3.5 Sonnet (content analysis)
- **Method:** Download audio for the top 5 outliers by view count. Transcribe via Deepgram. Pass each transcript to Claude with a structured analysis prompt extracting:
  - Hook strategy (first 60 seconds)
  - Narrative structure and beat pattern
  - Emotional triggers and audience retention tactics
  - Title/thumbnail relationship to content delivery
- **Output:** Individual analysis JSON files per video, plus full transcripts

**Why top 5?** Diminishing returns. The top 5 outliers represent 62% of all outlier views. Videos 6–17 follow the same patterns at lower magnitude.

| Component | Cost |
|-----------|------|
| Deepgram transcription (5 videos) | $0.55 |
| Claude analysis (5 prompts) | $0.16 |
| **Phase 3 total** | **$0.71** |

### Phase 4 — Synthesis

- **Tool:** Anthropic Claude 3.5 Sonnet
- **Method:** Feed all 5 individual analyses into a single synthesis prompt. Claude identifies cross-video patterns and generates the Creator Blueprint
- **Output:** `signal_report.json` — the final deliverable

Cost: **$0.03**.

---

## Total Pipeline Cost

| Phase | Cost |
|-------|------|
| Phase 1 — Cataloging | $0.00 |
| Phase 2 — Outlier Detection | $0.00 |
| Phase 3 — Transcription & Analysis | $0.71 |
| Phase 4 — Synthesis | $0.03 |
| **Total** | **$0.74** |

---

## Assumptions & Limitations

1. **View count as proxy for performance.** Views are the only universally public metric. Watch time, CTR, and subscriber conversion would improve signal quality but require creator-level access.
2. **Survivorship bias.** We analyze what worked. We do not analyze what failed — a deleted or unlisted video leaves no trace in the public catalog.
3. **Point-in-time snapshot.** View counts were captured on 2026-02-15. Viral trajectories and algorithmic promotion windows are not modeled.
4. **Single-channel scope.** SIGNAL v1 analyzes one channel. Cross-channel competitive analysis is a Phase 5 consideration.
5. **English-only.** Deepgram Nova-2 was configured for English transcription. Multilingual channels would require language detection preprocessing.

---

## Reproducibility

```bash
git clone https://github.com/Squillacky/deephammer-signal.git
cd deephammer-signal
cp .env.example .env  # Add your Deepgram + Anthropic API keys
uv sync
uv run python main.py



