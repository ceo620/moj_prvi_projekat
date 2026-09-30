from __future__ import annotations

import numpy as np
import pandas as pd


def add_credit_metrics(base_df: pd.DataFrame, debt_df: pd.DataFrame, opening_cash: float) -> pd.DataFrame:
    df = base_df.merge(debt_df[["year", "interest", "principal_repayment", "debt_service"]], on="year", how="left")
    df[["interest", "principal_repayment", "debt_service"]] = df[["interest", "principal_repayment", "debt_service"]].fillna(0.0)

    df["cfads"] = df["ufcf"] + df["interest"]
    df["dscr"] = np.where(df["debt_service"] > 0, df["cfads"] / df["debt_service"], np.nan)

    cash = opening_cash
    closing_cash = []
    for _, row in df.iterrows():
        cash = cash + row["ufcf"] - row["principal_repayment"] - row["interest"]
        closing_cash.append(round(cash, 2))

    df["closing_cash"] = closing_cash
    return df


def summary_metrics(df: pd.DataFrame, discount_rate: float | None = None) -> dict:
    result = {
        "min_dscr": float(df["dscr"].dropna().min()) if df["dscr"].notna().any() else None,
        "avg_dscr": float(df["dscr"].dropna().mean()) if df["dscr"].notna().any() else None,
        "final_cash": float(df["closing_cash"].iloc[-1]),
        "year_1_revenue": float(df["revenue"].iloc[0]),
        "year_n_revenue": float(df["revenue"].iloc[-1]),
        "year_1_ebitda": float(df["ebitda"].iloc[0]),
        "year_n_ebitda": float(df["ebitda"].iloc[-1]),
    }

    if discount_rate is not None:
        cash_flows = df["ufcf"].tolist()
        npv = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
        result["npv_ufcf"] = float(npv)
    return result
