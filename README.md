# SafeSpeedNet-AI Speed Safety Score

This focused repository contains the **Speed Safety Score** and road-segment classification system from SafeSpeedNet-AI.

Use this repository for the submission field:

```text
Speed Safety Score (Github link):
https://github.com/YOUR-USERNAME/safespeednet-speed-safety-score
```

## Purpose

The Speed Safety Score classifies every road segment into a safety-priority class using speed behaviour, traffic exposure, road-network structure, local context, vulnerability, and data uncertainty. It is designed for transport agencies that need an explainable first-pass screening layer for speed-limit review, enforcement planning, field verification, and engineering treatment prioritisation.

## What this repository contains

```text
safespeednet-speed-safety-score/
├── safespeednet_ai/
│   ├── scoring.py
│   └── utils.py
├── configs/scoring_default.yaml
├── docs/SPEED_SAFETY_SCORE.md
├── docs/CLASSIFICATION_SCHEMA.md
├── examples/score_segments_example.py
├── examples/example_input_segments.csv
├── examples/example_scored_segments.csv
├── tests/test_scoring.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Score formula

```text
Speed Safety Score =
35% speed behaviour risk
+ 25% traffic exposure risk
+ 20% structural network risk
+ 15% context and vulnerability risk
+ 5% data uncertainty risk
```

The score ranges from 0 to 100.

## Classification

| Score range | Class |
|---:|---|
| 0–30 | low |
| 31–50 | moderate |
| 51–70 | high |
| 71–100 | critical |

A road segment is flagged as `speed_unsafe_segment = 1` when its score exceeds the configured unsafe threshold or falls within the highest-risk quantile for the run.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Windows activation:

```bash
.venv\Scripts\activate
```

## Run the example

```bash
python examples/score_segments_example.py
```

This reads `examples/example_input_segments.csv` and writes `examples/example_scored_segments.csv`.

## Main code link for reviewers

The scoring implementation is in:

```text
safespeednet_ai/scoring.py
```

The key function is:

```python
build_risk_scores(frame, cfg_scoring)
```

It returns the risk components, `speed_safety_score`, `speed_safety_class`, `speed_unsafe_segment`, recommended safer speed, policy zone, reason codes, and review flag.
