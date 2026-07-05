from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def setup_logging(verbose: bool = True) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def first_existing(columns: Iterable[str], frame: pd.DataFrame) -> str | None:
    for col in columns:
        if col in frame.columns:
            return col
    return None


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def percentile_rank(values: pd.Series) -> pd.Series:
    s = pd.to_numeric(values, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series(np.zeros(len(s)), index=s.index, dtype="float64")
    return s.rank(pct=True).fillna(0.0).clip(0, 1)


def minmax(values: pd.Series) -> pd.Series:
    s = pd.to_numeric(values, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series(np.zeros(len(s)), index=s.index, dtype="float64")
    lo, hi = float(s.min()), float(s.max())
    if np.isclose(lo, hi):
        return pd.Series(np.zeros(len(s)), index=s.index, dtype="float64")
    return ((s - lo) / (hi - lo)).fillna(0.0).clip(0, 1)


def write_manifest(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
