GROK_PAYLOAD_V6_2 = {
  "version": "v6.2",
  "model_scope": "TITAN Central Brain Base",
  "locked_core": {
    "company": "ARS Metal DOO",
    "sponsor": "Hamza Yavuz",
    "reference_plant": "ADS Metal Turkey, Ankara",
    "factories": 3,
    "full_capacity_units_per_year": 3600,
    "base_capex_eur": 43560000,
    "p90_capex_eur": 51400000,
    "asp_eur_per_unit": 6200,
    "gross_margin": 0.48,
    "senior_debt_share": 0.62,
    "equity_share": 0.13,
    "grant_share": 0.25,
    "project_irr": 0.265,
    "equity_irr": 0.38,
    "min_dscr_locked": 1.95,
    "dscr_covenant": 1.35,
    "simple_payback_years": 3.6
  },
  "market_watch": {
    "estr_latest": 0.01932,
    "euribor_6m_latest": 0.02589,
    "euro_area_inflation_feb_2026": 0.019,
    "eur_try_latest": 51.4188,
    "eu_hrc_northern_europe_eur_t": 710.12,
    "eu_grid_investment_signal": "Positive",
    "transformer_demand_signal": "Strong",
    "europe_energy_shock_risk": "Elevated"
  },
  "working_lender_assumptions": {
    "debt_margin": 0.03,
    "debt_tenor_years": 10,
    "grace_years": 2,
    "amortization_start_year": 2030,
    "dsra_months": 6,
    "capex_draw_pct": {
      "2026": 0.15,
      "2027": 0.35,
      "2028": 0.35,
      "2029": 0.15
    },
    "cfads_conversion_from_gp": 0.7
  },
  "monte_carlo": {
    "iterations": 5000,
    "distributions": {
      "base_capex": {
        "type": "triangular",
        "min": 41500000,
        "mode": 43560000,
        "max": 51400000
      },
      "asp": {
        "type": "triangular",
        "min": 5580,
        "mode": 6200,
        "max": 6820
      },
      "gross_margin": {
        "type": "triangular",
        "min": 0.42,
        "mode": 0.48,
        "max": 0.52
      },
      "debt_base_rate": {
        "type": "triangular",
        "min": 0.017,
        "mode": 0.01932,
        "max": 0.03932
      },
      "steel_hrc": {
        "type": "triangular",
        "min": 650,
        "mode": 710.12,
        "max": 852.14
      },
      "ramp_delay_months": {
        "type": "discrete",
        "states": [
          0,
          3,
          6
        ],
        "probabilities": [
          0.6,
          0.25,
          0.15
        ]
      },
      "grant_delay_months": {
        "type": "discrete",
        "states": [
          0,
          6,
          12
        ],
        "probabilities": [
          0.6,
          0.3,
          0.1
        ]
      }
    },
    "summary": {
      "breach_probability_dscr_lt_1_35": 1.0,
      "review_probability_dscr_lt_1_95": 1.0,
      "p50_min_dscr": 1.0537097389450576,
      "p50_capex": 45120648.58106324,
      "p50_revenue_2030": 22331061.250399005
    }
  }
}