import pandas as pd

from safespeednet_ai.scoring import build_risk_scores


def test_build_risk_scores_outputs_required_fields():
    cfg = {
        "weights": {
            "speed_behavior": 0.35,
            "traffic_exposure": 0.25,
            "structural_network": 0.20,
            "context_vulnerability": 0.15,
            "data_uncertainty": 0.05,
        },
        "unsafe_threshold": 70,
        "top_quantile_unsafe": 0.90,
        "speed_classes_kmh": [30, 40, 50, 60, 70, 80, 90, 100],
    }
    df = pd.DataFrame(
        {
            "segment_uid": ["a", "b", "c"],
            "speed_limit_final": [50, 80, 30],
            "median_speed_final": [60, 75, 36],
            "f85_speed_final": [75, 88, 45],
            "percent_over_limit_final": [50, 10, 60],
            "weighted_sample_final": [1000, 100, 700],
            "sample_size_total_final": [1200, 150, 850],
            "edge_betweenness": [0.5, 0.1, 0.3],
            "edge_harmonic_closeness_mean": [0.7, 0.2, 0.4],
            "mean_degree": [4, 1, 3],
            "road_class_final": ["primary", "trunk", "service"],
            "land_use_final": ["commercial", "rural", "school"],
            "urban_pc_raw": [0.9, 0.1, 1.0],
            "helmet_vulnerability": [0.5, 0.4, 0.8],
            "imputation_confidence_mean": [0.9, 0.9, 0.9],
        }
    )
    out = build_risk_scores(df, cfg)
    required = [
        "speed_safety_score",
        "speed_safety_class",
        "speed_unsafe_segment",
        "context_speed_cap_kmh",
        "recommended_safe_speed_kmh",
        "speed_policy_zone",
        "reason_1",
        "review_required",
    ]
    for col in required:
        assert col in out.columns
    assert out["speed_safety_score"].between(0, 100).all()
