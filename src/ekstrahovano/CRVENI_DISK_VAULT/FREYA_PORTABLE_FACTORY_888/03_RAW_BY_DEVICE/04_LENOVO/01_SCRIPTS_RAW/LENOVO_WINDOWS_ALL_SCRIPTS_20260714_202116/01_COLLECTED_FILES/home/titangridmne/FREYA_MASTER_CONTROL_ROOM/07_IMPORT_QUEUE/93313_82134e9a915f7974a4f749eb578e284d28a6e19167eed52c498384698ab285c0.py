from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.calculations.io import load_assumptions
from src.calculations.operating import build_operating_projection
from src.calculations.debt import build_debt_schedule
from src.calculations.metrics import add_credit_metrics, summary_metrics


BASE_DIR = Path(__file__).resolve().parents[2]
ASSUMPTIONS_PATH = BASE_DIR / "data" / "assumptions" / "assumptions_master.csv"
OUTPUT_DIR = BASE_DIR / "outputs"


def main() -> None:
    assumptions = load_assumptions(ASSUMPTIONS_PATH)

    operating_df = build_operating_projection(assumptions)
    debt_df = build_debt_schedule(
        principal=float(assumptions["opening_debt"]),
        annual_rate=float(assumptions["debt_interest_rate"]),
        tenor_years=int(assumptions["debt_tenor_years"]),
        start_year=int(assumptions["start_year"]),
        periods=int(assumptions["projection_years"]),
    )
    model_df = add_credit_metrics(
        base_df=operating_df,
        debt_df=debt_df,
        opening_cash=float(assumptions["opening_cash"]),
    )
    metrics = summary_metrics(model_df, discount_rate=float(assumptions["debt_interest_rate"]))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_df.to_csv(OUTPUT_DIR / "phase2_model_output.csv", index=False)
    debt_df.to_csv(OUTPUT_DIR / "phase2_debt_schedule.csv", index=False)
    pd.DataFrame([metrics]).to_csv(OUTPUT_DIR / "phase2_summary_metrics.csv", index=False)

    print("Model run complete.")
    print(model_df.to_string(index=False))
    print("\nSummary metrics:")
    for key, value in metrics.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
