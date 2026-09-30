from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_assumptions(csv_path: str | Path) -> dict:
    """Load assumptions from a parameter/value CSV into a typed dictionary."""
    df = pd.read_csv(csv_path)
    required = {"parameter", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Assumptions file missing columns: {sorted(missing)}")

    assumptions: dict[str, float | int | str] = {}
    for _, row in df.iterrows():
        key = str(row["parameter"]).strip()
        raw = row["value"]
        assumptions[key] = _coerce_value(raw)
    return assumptions


def _coerce_value(value):
    if pd.isna(value):
        return value
    try:
        numeric = float(value)
        if numeric.is_integer():
            return int(numeric)
        return numeric
    except Exception:
        return value
