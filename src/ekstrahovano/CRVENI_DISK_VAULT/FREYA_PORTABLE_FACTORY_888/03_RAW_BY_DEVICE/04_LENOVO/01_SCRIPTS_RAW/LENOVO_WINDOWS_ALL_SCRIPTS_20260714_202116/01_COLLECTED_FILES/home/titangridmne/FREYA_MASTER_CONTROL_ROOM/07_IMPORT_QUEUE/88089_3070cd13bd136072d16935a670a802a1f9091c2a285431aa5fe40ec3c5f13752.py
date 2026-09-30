from __future__ import annotations

import numpy as np
import pandas as pd


def annuity_payment(principal: float, annual_rate: float, tenor_years: int) -> float:
    """Return constant annual debt service for a standard annuity loan."""
    if tenor_years <= 0:
        raise ValueError("tenor_years must be positive")
    if principal <= 0:
        return 0.0
    if annual_rate == 0:
        return principal / tenor_years
    factor = annual_rate / (1 - (1 + annual_rate) ** (-tenor_years))
    return principal * factor


def build_debt_schedule(principal: float, annual_rate: float, tenor_years: int, start_year: int, periods: int) -> pd.DataFrame:
    """Build an annual debt schedule over the requested forecast periods."""
    payment = annuity_payment(principal, annual_rate, tenor_years)
    rows = []
    opening = principal

    for i in range(periods):
        year = start_year + i
        if i < tenor_years and opening > 0:
            interest = opening * annual_rate
            principal_repaid = min(payment - interest, opening)
            total_service = interest + principal_repaid
            closing = max(opening - principal_repaid, 0.0)
        else:
            interest = 0.0
            principal_repaid = 0.0
            total_service = 0.0
            closing = 0.0

        rows.append(
            {
                "year": year,
                "opening_debt": round(opening, 2),
                "interest": round(interest, 2),
                "principal_repayment": round(principal_repaid, 2),
                "debt_service": round(total_service, 2),
                "closing_debt": round(closing, 2),
            }
        )
        opening = closing

    return pd.DataFrame(rows)
