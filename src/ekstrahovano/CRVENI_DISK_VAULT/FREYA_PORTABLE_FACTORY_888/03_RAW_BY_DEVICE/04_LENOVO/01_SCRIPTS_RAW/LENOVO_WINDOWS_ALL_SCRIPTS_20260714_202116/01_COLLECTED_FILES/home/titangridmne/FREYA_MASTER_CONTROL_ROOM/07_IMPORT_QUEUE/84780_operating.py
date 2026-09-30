from __future__ import annotations

import pandas as pd


def build_operating_projection(assumptions: dict) -> pd.DataFrame:
    start_year = int(assumptions["start_year"])
    years = int(assumptions["projection_years"])
    starting_units = float(assumptions["starting_units"])
    growth = float(assumptions["annual_unit_growth"])
    price = float(assumptions["price_per_unit"])
    cogs_pct = float(assumptions["cogs_pct_of_revenue"])
    fixed_opex = float(assumptions["fixed_opex"])
    dep = float(assumptions["depreciation"])
    tax_rate = float(assumptions["tax_rate"])
    capex = float(assumptions["capex"])
    wc_pct = float(assumptions["working_capital_pct_of_revenue"])

    rows = []
    previous_wc = 0.0

    for i in range(years):
        year = start_year + i
        units = starting_units * ((1 + growth) ** i)
        revenue = units * price
        cogs = revenue * cogs_pct
        gross_profit = revenue - cogs
        ebitda = gross_profit - fixed_opex
        ebit = ebitda - dep
        tax = max(ebit, 0.0) * tax_rate
        nopat = ebit - tax
        operating_cf_before_wc = nopat + dep
        working_capital = revenue * wc_pct
        wc_movement = working_capital - previous_wc
        ufcf = operating_cf_before_wc - wc_movement - capex

        rows.append(
            {
                "year": year,
                "units": round(units, 2),
                "revenue": round(revenue, 2),
                "cogs": round(cogs, 2),
                "gross_profit": round(gross_profit, 2),
                "fixed_opex": round(fixed_opex, 2),
                "ebitda": round(ebitda, 2),
                "depreciation": round(dep, 2),
                "ebit": round(ebit, 2),
                "tax": round(tax, 2),
                "nopat": round(nopat, 2),
                "working_capital": round(working_capital, 2),
                "wc_movement": round(wc_movement, 2),
                "capex": round(capex, 2),
                "ufcf": round(ufcf, 2),
            }
        )
        previous_wc = working_capital

    return pd.DataFrame(rows)
