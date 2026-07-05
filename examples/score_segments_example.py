from pathlib import Path
import pandas as pd
import yaml

from safespeednet_ai.scoring import build_risk_scores

ROOT = Path(__file__).resolve().parents[1]
input_path = ROOT / "examples" / "example_input_segments.csv"
output_path = ROOT / "examples" / "example_scored_segments.csv"
config_path = ROOT / "configs" / "scoring_default.yaml"

with config_path.open("r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)["scoring"]

segments = pd.read_csv(input_path)
scored = build_risk_scores(segments, cfg)
scored.to_csv(output_path, index=False)

print(f"Wrote {output_path}")
print(scored[["segment_uid", "speed_safety_score", "speed_safety_class", "speed_unsafe_segment", "recommended_safe_speed_kmh", "reason_1"]])
