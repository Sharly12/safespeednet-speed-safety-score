from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import percentile_rank


LANDUSE_RISK = {
    "school": 1.00,
    "market": 0.98,
    "residential": 0.95,
    "urban": 0.95,
    "mixed": 0.90,
    "commercial": 0.85,
    "industrial": 0.65,
    "rural": 0.35,
    "agriculture": 0.35,
    "forest": 0.25,
    "unknown": 0.55,
}

ROADCLASS_SENSITIVITY = {
    "living_street": 1.00,
    "residential": 0.95,
    "local": 0.90,
    "service": 0.85,
    "unclassified": 0.70,
    "tertiary": 0.70,
    "secondary": 0.60,
    "primary": 0.50,
    "trunk": 0.35,
    "motorway": 0.20,
    "unknown": 0.65,
}


def _series(frame: pd.DataFrame, col: str, default, dtype: str | None = None) -> pd.Series:
    if col in frame.columns:
        s = frame[col]
    else:
        s = pd.Series(default, index=frame.index)
    if dtype == "numeric":
        return pd.to_numeric(s, errors="coerce")
    return s


def _text(series: pd.Series) -> pd.Series:
    return series.astype("object").where(series.notna(), "unknown").astype(str).str.lower()


def _contains_any(text: str, keys: list[str]) -> bool:
    return any(k in text for k in keys)


def _map_text_risk(series: pd.Series, mapping: dict[str, float], default: float) -> pd.Series:
    def map_one(x) -> float:
        text = str(x).lower()
        for key, val in mapping.items():
            if key in text:
                return val
        return default

    return series.apply(map_one).astype("float64")


def _first_density_col(frame: pd.DataFrame) -> str | None:
    density_cols = [c for c in frame.columns if c.startswith("road_density_")]
    return density_cols[0] if density_cols else None


def derive_urban_context_score(out: pd.DataFrame) -> pd.Series:
    """Build a town/urban-context proxy from land use, urban percentage and network form.

    This intentionally does not depend only on a LandUse column. In many road
    datasets land use is missing or coarse, so local road density and junction
    complexity are used as spatial evidence of town/urban context.
    """
    landuse_txt = _text(_series(out, "land_use_final", "unknown"))
    roadclass_txt = _text(_series(out, "road_class_final", "unknown"))

    landuse_urban = pd.Series(0.0, index=out.index)
    landuse_urban[landuse_txt.str.contains("school|market|residential|urban|mixed|commercial", regex=True)] = 1.0
    landuse_urban[landuse_txt.str.contains("industrial", regex=False)] = 0.65
    landuse_urban[landuse_txt.str.contains("rural|agriculture|forest", regex=True)] = 0.15

    urban_pc = pd.to_numeric(_series(out, "urban_pc_raw", 0), errors="coerce").fillna(0)
    urban_pc = pd.Series(np.where(urban_pc > 1, urban_pc / 100.0, urban_pc), index=out.index).clip(0, 1)

    density_col = _first_density_col(out)
    road_density_rank = percentile_rank(out[density_col]) if density_col else pd.Series(0.0, index=out.index)

    degree_rank = percentile_rank(_series(out, "mean_degree", 0, dtype="numeric").fillna(0))

    roadclass_urban = pd.Series(0.35, index=out.index)
    roadclass_urban[roadclass_txt.str.contains("living_street|residential|local|service", regex=True)] = 0.85
    roadclass_urban[roadclass_txt.str.contains("tertiary|unclassified", regex=True)] = 0.65
    roadclass_urban[roadclass_txt.str.contains("secondary|primary", regex=True)] = 0.45
    roadclass_urban[roadclass_txt.str.contains("trunk|motorway", regex=True)] = 0.25

    urban_context = (
        0.30 * landuse_urban
        + 0.25 * urban_pc
        + 0.25 * road_density_rank
        + 0.10 * degree_rank
        + 0.10 * roadclass_urban
    ).clip(0, 1)

    return urban_context.astype("float64")


def build_risk_scores(frame: pd.DataFrame, cfg_scoring: dict) -> pd.DataFrame:
    out = frame.copy()

    speed_limit = pd.to_numeric(_series(out, "speed_limit_final", np.nan), errors="coerce")
    median = pd.to_numeric(_series(out, "median_speed_final", np.nan), errors="coerce")
    f85 = pd.to_numeric(_series(out, "f85_speed_final", np.nan), errors="coerce")
    pct_over = pd.to_numeric(_series(out, "percent_over_limit_final", 0), errors="coerce").fillna(0)
    weighted = pd.to_numeric(_series(out, "weighted_sample_final", 0), errors="coerce").fillna(0)
    sample_total = pd.to_numeric(_series(out, "sample_size_total_final", np.nan), errors="coerce").fillna(weighted)

    median = median.fillna(speed_limit).fillna(0)
    f85 = f85.fillna(median).fillna(speed_limit).fillna(0)
    speed_limit = speed_limit.fillna(median).fillna(0)

    out["speed_pressure"] = (f85 - speed_limit).clip(lower=0)
    out["median_speed_pressure"] = (median - speed_limit).clip(lower=0)

    speed_pressure_score = percentile_rank(out["speed_pressure"])
    median_pressure_score = percentile_rank(out["median_speed_pressure"])
    pct_over_score = percentile_rank(pct_over)
    out["speed_behavior_risk"] = (
        0.45 * speed_pressure_score + 0.25 * median_pressure_score + 0.30 * pct_over_score
    ).clip(0, 1)

    out["traffic_exposure_risk"] = (
        0.65 * percentile_rank(weighted) + 0.35 * percentile_rank(sample_total)
    ).clip(0, 1)

    betw = percentile_rank(_series(out, "edge_betweenness", 0, dtype="numeric").fillna(0))
    close = percentile_rank(_series(out, "edge_harmonic_closeness_mean", 0, dtype="numeric").fillna(0))
    degree = percentile_rank(_series(out, "mean_degree", 0, dtype="numeric").fillna(0))
    density_col = _first_density_col(out)
    density = percentile_rank(out[density_col]) if density_col else pd.Series(0, index=out.index)
    bridge = pd.to_numeric(_series(out, "bridge_edge_flag", 0), errors="coerce").fillna(0)
    dead_end = pd.to_numeric(_series(out, "dead_end_flag", 0), errors="coerce").fillna(0)
    out["structural_network_risk"] = (
        0.30 * betw + 0.18 * close + 0.12 * degree + 0.25 * density + 0.10 * bridge + 0.05 * dead_end
    ).clip(0, 1)

    landuse = _series(out, "land_use_final", "unknown")
    roadclass = _series(out, "road_class_final", "unknown")
    landuse_risk = _map_text_risk(landuse, LANDUSE_RISK, 0.55)
    roadclass_risk = _map_text_risk(roadclass, ROADCLASS_SENSITIVITY, 0.65)
    helmet_vuln = pd.to_numeric(_series(out, "helmet_vulnerability", 0.5), errors="coerce").fillna(0.5)
    out["urban_context_score"] = derive_urban_context_score(out)

    out["context_vulnerability_risk"] = (
        0.30 * landuse_risk
        + 0.20 * roadclass_risk
        + 0.20 * helmet_vuln
        + 0.30 * out["urban_context_score"]
    ).clip(0, 1)

    imputation_conf = pd.to_numeric(_series(out, "imputation_confidence_mean", 1), errors="coerce").fillna(1)
    connector = pd.to_numeric(_series(out, "connector_used_flag", 0), errors="coerce").fillna(0)
    out["data_uncertainty_risk"] = (0.75 * (1.0 - imputation_conf) + 0.25 * connector).clip(0, 1)

    weights = cfg_scoring.get("weights", {})
    score01 = (
        float(weights.get("speed_behavior", 0.35)) * out["speed_behavior_risk"]
        + float(weights.get("traffic_exposure", 0.25)) * out["traffic_exposure_risk"]
        + float(weights.get("structural_network", 0.20)) * out["structural_network_risk"]
        + float(weights.get("context_vulnerability", 0.15)) * out["context_vulnerability_risk"]
        + float(weights.get("data_uncertainty", 0.05)) * out["data_uncertainty_risk"]
    )
    out["speed_safety_score"] = (100 * score01).round(2)

    bins = [-0.01, 30, 50, 70, 100]
    labels = ["low", "moderate", "high", "critical"]
    out["speed_safety_class"] = pd.cut(out["speed_safety_score"], bins=bins, labels=labels).astype(str)

    unsafe_threshold = float(cfg_scoring.get("unsafe_threshold", 70))
    quantile_thr = out["speed_safety_score"].quantile(float(cfg_scoring.get("top_quantile_unsafe", 0.90)))
    threshold = min(unsafe_threshold, quantile_thr) if len(out) else unsafe_threshold
    out["speed_unsafe_segment"] = (out["speed_safety_score"] >= threshold).astype(int)

    out["context_speed_cap_kmh"] = context_speed_cap(out, cfg_scoring)
    out["recommended_safe_speed_kmh"] = recommend_speed_classes(out, cfg_scoring)
    out["speed_reduction_from_existing_kmh"] = (
        pd.to_numeric(_series(out, "speed_limit_final", np.nan), errors="coerce") - out["recommended_safe_speed_kmh"]
    ).clip(lower=0)
    out["speed_policy_zone"] = out.apply(policy_zone_label, axis=1)

    out["reason_1"], out["reason_2"], out["reason_3"] = zip(*out.apply(reason_codes, axis=1))
    out["review_required"] = (
        (out["speed_unsafe_segment"].eq(1))
        | (out["data_uncertainty_risk"] > 0.55)
        | (out.get("main_component_flag", pd.Series(True, index=out.index)).eq(False))
        | (out["speed_reduction_from_existing_kmh"] >= 20)
    ).astype(int)
    return out


def _base_roadclass_cap(roadclass_text: str, classes: list[int]) -> int:
    t = str(roadclass_text).lower()
    if _contains_any(t, ["living_street", "residential"]):
        cap = 30
    elif _contains_any(t, ["service", "local"]):
        cap = 40
    elif "tertiary" in t or "unclassified" in t:
        cap = 60
    elif "secondary" in t:
        cap = 70
    elif "primary" in t:
        cap = 80
    elif "trunk" in t:
        cap = 90
    elif "motorway" in t:
        cap = 100
    else:
        cap = 70
    return _floor_to_class(cap, classes)


def context_speed_cap(out: pd.DataFrame, cfg_scoring: dict) -> pd.Series:
    classes = sorted([int(x) for x in cfg_scoring.get("speed_classes_kmh", [30, 40, 50, 60, 70, 80])])
    landuse_txt = _text(_series(out, "land_use_final", "unknown"))
    roadclass_txt = _text(_series(out, "road_class_final", "unknown"))
    urban_context = pd.to_numeric(_series(out, "urban_context_score", 0), errors="coerce").fillna(0)

    caps = []
    for idx in out.index:
        lu = landuse_txt.loc[idx]
        rc = roadclass_txt.loc[idx]
        u = float(urban_context.loc[idx])
        cap = _base_roadclass_cap(rc, classes)

        major = _contains_any(rc, ["motorway", "trunk", "primary"])
        secondary = "secondary" in rc
        tertiary = "tertiary" in rc or "unclassified" in rc
        local = _contains_any(rc, ["living_street", "residential", "service", "local"])

        if _contains_any(lu, ["school", "market"]):
            cap = min(cap, 30)
        elif "residential" in lu or "living_street" in rc:
            cap = min(cap, 40)
        elif _contains_any(lu, ["urban", "mixed", "commercial"]):
            cap = min(cap, 60 if major else 50)

        if u >= 0.80:
            if major:
                cap = min(cap, 60)
            elif secondary:
                cap = min(cap, 50)
            elif tertiary:
                cap = min(cap, 50)
            elif local:
                cap = min(cap, 40)
            else:
                cap = min(cap, 50)
        elif u >= 0.60:
            if major:
                cap = min(cap, 70)
            elif secondary:
                cap = min(cap, 60)
            elif tertiary:
                cap = min(cap, 50)
            elif local:
                cap = min(cap, 40)
            else:
                cap = min(cap, 60)
        elif u >= 0.40:
            if major:
                cap = min(cap, 80)
            elif secondary:
                cap = min(cap, 70)
            elif tertiary:
                cap = min(cap, 60)
            elif local:
                cap = min(cap, 50)
            else:
                cap = min(cap, 70)

        caps.append(_floor_to_class(cap, classes))

    return pd.Series(caps, index=out.index, dtype="int64")


def _floor_to_class(value: float, classes: list[int]) -> int:
    value = float(value)
    eligible = [c for c in classes if c <= value]
    if eligible:
        return int(max(eligible))
    return int(min(classes))


def recommend_speed_classes(out: pd.DataFrame, cfg_scoring: dict) -> pd.Series:
    """Recommend a safer speed class using context caps plus risk-based reductions.

    The previous implementation reduced the current speed only when the total
    safety score was high. That allowed moderate-score urban/town roads to keep
    80–90 km/h. This version first applies a land-use/urban/network-context cap,
    then applies additional reductions for overspeeding, exposure and structural
    priority.
    """
    classes = sorted([int(x) for x in cfg_scoring.get("speed_classes_kmh", [30, 40, 50, 60, 70, 80])])
    current = pd.to_numeric(_series(out, "speed_limit_final", np.nan), errors="coerce")
    fallback = float(np.nanmedian(classes))
    current = current.fillna(fallback)

    cap = pd.to_numeric(_series(out, "context_speed_cap_kmh", max(classes)), errors="coerce").fillna(max(classes))
    rec = np.minimum(current, cap)

    score = pd.to_numeric(_series(out, "speed_safety_score", 0), errors="coerce").fillna(0)
    speed_risk = pd.to_numeric(_series(out, "speed_behavior_risk", 0), errors="coerce").fillna(0)
    exposure = pd.to_numeric(_series(out, "traffic_exposure_risk", 0), errors="coerce").fillna(0)
    structure = pd.to_numeric(_series(out, "structural_network_risk", 0), errors="coerce").fillna(0)
    context = pd.to_numeric(_series(out, "context_vulnerability_risk", 0), errors="coerce").fillna(0)
    urban = pd.to_numeric(_series(out, "urban_context_score", 0), errors="coerce").fillna(0)

    rec = np.where(score >= 85, rec - 20, rec)
    rec = np.where((score >= 70) & (score < 85), rec - 10, rec)
    rec = np.where((speed_risk >= 0.75) & (exposure >= 0.60), rec - 10, rec)
    rec = np.where((structure >= 0.75) & (context >= 0.60), rec - 10, rec)
    rec = np.where((urban >= 0.75) & (speed_risk >= 0.60), rec - 10, rec)

    rec = pd.Series(rec, index=out.index).clip(lower=min(classes), upper=max(classes))
    return rec.apply(lambda x: _floor_to_class(x, classes)).astype(int)


def policy_zone_label(row: pd.Series) -> str:
    lu = str(row.get("land_use_final", "unknown")).lower()
    rc = str(row.get("road_class_final", "unknown")).lower()
    u = float(row.get("urban_context_score", 0) or 0)
    if _contains_any(lu, ["school", "market"]):
        return "sensitive pedestrian zone"
    if _contains_any(lu, ["residential"]) or _contains_any(rc, ["living_street", "residential"]):
        return "residential/local street"
    if u >= 0.80:
        return "dense urban/town road"
    if u >= 0.60:
        return "urban/peri-urban road"
    if _contains_any(rc, ["motorway", "trunk", "primary"]):
        return "major corridor"
    return "lower-density road context"


def reason_codes(row: pd.Series) -> tuple[str, str, str]:
    current_speed = row.get("speed_limit_final", np.nan)
    rec_speed = row.get("recommended_safe_speed_kmh", np.nan)
    cap = row.get("context_speed_cap_kmh", np.nan)

    candidates: list[tuple[float, str]] = []

    try:
        if pd.notna(current_speed) and pd.notna(cap) and float(cap) < float(current_speed):
            candidates.append((1.25, "land-use / town-context speed cap"))
    except Exception:
        pass

    if row.get("urban_context_score", 0) >= 0.75:
        candidates.append((1.15, "dense urban road environment"))
    elif row.get("urban_context_score", 0) >= 0.60:
        candidates.append((1.05, "urban / peri-urban road context"))

    candidates.extend(
        [
            (row.get("speed_behavior_risk", 0), "high overspeeding pressure"),
            (row.get("traffic_exposure_risk", 0), "high traffic exposure"),
            (row.get("structural_network_risk", 0), "important network location"),
            (row.get("context_vulnerability_risk", 0), "sensitive land-use / vulnerable users"),
            (row.get("data_uncertainty_risk", 0), "data uncertainty requires review"),
        ]
    )

    ordered = []
    for _, label in sorted(candidates, reverse=True):
        if label not in ordered:
            ordered.append(label)
        if len(ordered) == 3:
            break

    while len(ordered) < 3:
        ordered.append("lower relative concern")

    return ordered[0], ordered[1], ordered[2]
