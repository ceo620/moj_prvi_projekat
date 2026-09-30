#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_DECISION_ENGINE_v1.py

TITAN 11 - Decision Intelligence Layer v1
Author: ARS / TITAN 11
Purpose:
    Converts SSOT signal extraction output into audit-grade decision intelligence.

Input:
    - Excel (.xlsx) or CSV containing TITAN SSOT signals with expected columns:
        Signal_ID
        Entity_Category
        Canonical_Value
        Confidence_Score (POA)
        Nearby_Keywords
        SSOT_Status
        Strategic_Impact

Output:
    - Excel workbook with sheets:
        01_DECISION_TABLE
        02_RISK_LAYER
        03_GAP_ANALYSIS
        04_EXECUTIVE_SUMMARY
        05_AUDIT_LOG
    - JSON audit log

Usage:
    python TITAN_DECISION_ENGINE_v1.py --input TITAN_SSOT_Signal_Extraction_Clean_v55.xlsx
    python TITAN_DECISION_ENGINE_v1.py --input signals.csv --output TITAN_Decision_Output.xlsx
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


ENGINE_VERSION = "1.0"
SCHEMA_VERSION = "TITAN_DECISION_SCHEMA_v1"
DEFAULT_OUTPUT = "TITAN_Decision_Engine_v1_Output.xlsx"
DEFAULT_AUDIT_JSON = "TITAN_Decision_Engine_v1_Audit_Log.json"


REQUIRED_COLUMNS = [
    "Signal_ID",
    "Entity_Category",
    "Canonical_Value",
    "Confidence_Score (POA)",
    "Nearby_Keywords",
    "SSOT_Status",
    "Strategic_Impact",
]


CRITICAL_DOCUMENT_KEYWORDS = {
    "financial_model": [
        "financial model", "npv", "irr", "wacc", "dscr", "cash flow", "projection",
        "model", "finansijski model", "projekcija", "diskont"
    ],
    "capex": [
        "capex", "equipment", "civil works", "machinery", "asset", "procurement",
        "investment cost", "capital expenditure", "oprema", "gradnja", "investicija"
    ],
    "legal_ownership": [
        "ownership", "title", "land", "permit", "license", "concession",
        "property", "legal", "vlasništvo", "dozvola", "zemljište", "ugovor"
    ],
    "environmental_social": [
        "esg", "environment", "environmental", "social", "eia", "esia", "ifc",
        "ebrd", "equator principles", "životna sredina", "ekologija"
    ],
    "technical_feasibility": [
        "technical", "feasibility", "engineering", "design", "grid", "transformer",
        "capacity", "specification", "tehnički", "studija", "projektovanje"
    ],
    "procurement": [
        "procurement", "tender", "supplier", "vendor", "contractor", "quotation",
        "nabavka", "dobavljač", "tender", "ponuda"
    ],
    "risk_register": [
        "risk", "sensitivity", "scenario", "mitigation", "insurance", "hedging",
        "rizik", "osjetljivost", "scenario", "ublažavanje"
    ],
    "permits_approvals": [
        "approval", "permit", "license", "consent", "urban", "construction permit",
        "odobrenje", "dozvola", "saglasnost", "urbanistički"
    ],
}


DECISION_RULES = [
    {
        "decision_type": "CAPEX_CONFIRMATION",
        "keywords": ["capex", "equipment", "civil", "construction", "machinery", "asset", "procurement", "investment", "oprema", "gradnja"],
        "base_impact": "Direct impact on total investment cost, depreciation base, financing need and procurement plan.",
    },
    {
        "decision_type": "FINANCIAL_BANKABILITY",
        "keywords": ["npv", "irr", "wacc", "dscr", "ebitda", "cash flow", "loan", "debt", "equity", "grant", "financing", "kredit"],
        "base_impact": "Direct impact on lender assessment, debt capacity, covenant structure and sponsor contribution.",
    },
    {
        "decision_type": "LEGAL_COMPLIANCE",
        "keywords": ["legal", "contract", "permit", "license", "ownership", "land", "concession", "procurement law", "ugovor", "dozvola"],
        "base_impact": "Direct impact on enforceability, permitting, title risk, procurement compliance and transaction closing.",
    },
    {
        "decision_type": "ESG_EBRD_IFC",
        "keywords": ["esg", "environment", "social", "eia", "esia", "ifc", "ebrd", "eib", "resettlement", "stakeholder"],
        "base_impact": "Direct impact on EIB/EBRD eligibility, disclosure requirements, environmental approvals and reputational risk.",
    },
    {
        "decision_type": "TECHNICAL_FEASIBILITY",
        "keywords": ["technical", "engineering", "grid", "transformer", "capacity", "design", "testing", "commissioning", "tehnički"],
        "base_impact": "Direct impact on implementation feasibility, schedule reliability, equipment specification and production readiness.",
    },
    {
        "decision_type": "PROCUREMENT_READINESS",
        "keywords": ["supplier", "vendor", "quotation", "tender", "procurement", "contractor", "delivery", "lead time", "nabavka"],
        "base_impact": "Direct impact on procurement transparency, delivery risk, cost certainty and implementation schedule.",
    },
    {
        "decision_type": "RISK_CONTROL",
        "keywords": ["risk", "sensitivity", "scenario", "mitigation", "insurance", "hedging", "political", "inflation", "fx"],
        "base_impact": "Direct impact on downside protection, sovereign-risk buffer, contingency and lender risk appetite.",
    },
]


@dataclass
class DecisionRecord:
    Decision_ID: str
    Signal_Reference: str
    Decision_Type: str
    Final_Value: str
    Confidence: float
    Risk_Level: str
    Impact: str
    SSOT_Status: str
    Entity_Category: str
    Rule_Basis: str


@dataclass
class RiskRecord:
    Risk_ID: str
    Signal_Reference: str
    Risk_Category: str
    Risk_Level: str
    Risk_Reason: str
    Mitigation_Action: str
    Confidence: float


@dataclass
class GapRecord:
    Gap_ID: str
    Required_Area: str
    Status: str
    Evidence_Count: int
    Risk_Level: str
    Recommended_Action: str


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_status(value: Any) -> str:
    text = normalize_text(value).upper()
    if "LOCKED" in text:
        return "LOCKED"
    if "DRAFT" in text:
        return "DRAFT"
    return "DRAFT"


def parse_confidence(value: Any) -> float:
    if pd.isna(value):
        return 0.50
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    text = str(value).replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0.50
    number = float(match.group(1))
    if number > 1:
        number = number / 100.0
    return max(0.0, min(1.0, number))


def load_signals(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix in [".xlsx", ".xlsm", ".xls"]:
        workbook = pd.ExcelFile(input_path)
        preferred = None
        for sheet in workbook.sheet_names:
            sample = pd.read_excel(input_path, sheet_name=sheet, nrows=5)
            if any(str(c).strip() in REQUIRED_COLUMNS for c in sample.columns):
                preferred = sheet
                break
        if preferred is None:
            preferred = workbook.sheet_names[0]
        df = pd.read_excel(input_path, sheet_name=preferred)
    elif suffix == ".csv":
        df = pd.read_csv(input_path)
    else:
        raise ValueError("Unsupported input format. Use .xlsx, .xls, .xlsm or .csv")

    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required SSOT columns: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df = df.dropna(how="all")

    for col in REQUIRED_COLUMNS:
        if col != "Confidence_Score (POA)":
            df[col] = df[col].map(normalize_text)

    df["Confidence_Score (POA)"] = df["Confidence_Score (POA)"].map(parse_confidence)
    df["SSOT_Status"] = df["SSOT_Status"].map(normalize_status)

    # Remove repeated headers/malformed rows.
    df = df[df["Signal_ID"].str.upper() != "SIGNAL_ID"]
    df = df[df["Canonical_Value"].str.len() > 0]

    # Deduplicate by canonical content + category, keeping higher confidence and LOCKED over DRAFT.
    df["_status_rank"] = df["SSOT_Status"].map({"LOCKED": 2, "DRAFT": 1}).fillna(0)
    df["_dedupe_key"] = (
        df["Entity_Category"].str.lower().str.strip()
        + "||"
        + df["Canonical_Value"].str.lower().str.strip()
    )
    df = df.sort_values(
        by=["_dedupe_key", "_status_rank", "Confidence_Score (POA)"],
        ascending=[True, False, False],
    )
    df = df.drop_duplicates(subset=["_dedupe_key"], keep="first")
    df = df.drop(columns=["_status_rank", "_dedupe_key"])

    return df.reset_index(drop=True)


def combined_signal_text(row: pd.Series) -> str:
    return " ".join(
        [
            normalize_text(row.get("Entity_Category", "")),
            normalize_text(row.get("Canonical_Value", "")),
            normalize_text(row.get("Nearby_Keywords", "")),
            normalize_text(row.get("Strategic_Impact", "")),
        ]
    ).lower()


def classify_decision_type(row: pd.Series) -> Tuple[str, str, str]:
    text = combined_signal_text(row)
    scores = []

    for rule in DECISION_RULES:
        hits = [kw for kw in rule["keywords"] if kw.lower() in text]
        if hits:
            scores.append((len(hits), rule["decision_type"], rule["base_impact"], ", ".join(hits)))

    if not scores:
        return (
            "GENERAL_SSOT_VALIDATION",
            "Generic SSOT evidence requiring classification by analyst or next kernel layer.",
            "No specific rule hit; default validation logic.",
        )

    scores.sort(reverse=True, key=lambda item: item[0])
    _, decision_type, impact, hit_basis = scores[0]
    return decision_type, impact, f"Keyword rule hit: {hit_basis}"


def assign_risk_level(confidence: float, status: str, decision_type: str, value: str) -> Tuple[str, str]:
    value_lower = value.lower()
    negative_markers = [
        "missing", "not available", "unknown", "conflict", "incomplete", "draft",
        "nedostaje", "nepoznato", "konflikt", "nepotpuno"
    ]

    has_negative_marker = any(marker in value_lower for marker in negative_markers)

    if confidence < 0.65 or status != "LOCKED" or has_negative_marker:
        if decision_type in ["LEGAL_COMPLIANCE", "ESG_EBRD_IFC", "FINANCIAL_BANKABILITY"]:
            return "HIGH", "Critical lender-facing area with low confidence, DRAFT status or adverse marker."
        return "MEDIUM", "Signal requires review due to low confidence, DRAFT status or adverse marker."

    if confidence < 0.80:
        return "MEDIUM", "Moderate confidence; acceptable for working layer but not final bank package."

    return "LOW", "High-confidence LOCKED signal with no adverse marker detected."


def mitigation_for(decision_type: str, risk_level: str) -> str:
    if risk_level == "LOW":
        return "Maintain in SSOT and include as supporting evidence in investor/lender package."

    actions = {
        "CAPEX_CONFIRMATION": "Reconcile with vendor quotations, CBS code, procurement package and contingency reserve.",
        "FINANCIAL_BANKABILITY": "Validate against financial model, DSCR covenant, WACC assumptions and sensitivity analysis.",
        "LEGAL_COMPLIANCE": "Obtain or verify legal document, ownership evidence, permit, contract or counsel opinion.",
        "ESG_EBRD_IFC": "Map evidence to EBRD/EIB/IFC requirements; prepare missing ESIA/EIA/stakeholder documentation.",
        "TECHNICAL_FEASIBILITY": "Validate with engineering design, capacity calculation, grid interface and commissioning plan.",
        "PROCUREMENT_READINESS": "Attach tender file, supplier benchmark, lead time evidence and procurement compliance note.",
        "RISK_CONTROL": "Add mitigation owner, residual risk score, scenario sensitivity and contingency allocation.",
        "GENERAL_SSOT_VALIDATION": "Assign analyst owner and reclassify after document-level verification.",
    }
    return actions.get(decision_type, "Escalate to analyst for manual validation and evidence strengthening.")


def build_decision_table(df: pd.DataFrame) -> pd.DataFrame:
    records: List[DecisionRecord] = []

    for idx, row in df.iterrows():
        signal_id = normalize_text(row["Signal_ID"]) or f"SIGNAL_{idx+1:05d}"
        confidence = parse_confidence(row["Confidence_Score (POA)"])
        status = normalize_status(row["SSOT_Status"])
        decision_type, impact_base, rule_basis = classify_decision_type(row)
        risk_level, risk_reason = assign_risk_level(
            confidence=confidence,
            status=status,
            decision_type=decision_type,
            value=normalize_text(row["Canonical_Value"]),
        )

        impact = normalize_text(row["Strategic_Impact"])
        if not impact:
            impact = impact_base
        else:
            impact = f"{impact} | Decision interpretation: {impact_base}"

        records.append(
            DecisionRecord(
                Decision_ID=f"DEC-{idx+1:05d}",
                Signal_Reference=signal_id,
                Decision_Type=decision_type,
                Final_Value=normalize_text(row["Canonical_Value"]),
                Confidence=round(confidence, 4),
                Risk_Level=risk_level,
                Impact=impact,
                SSOT_Status=status,
                Entity_Category=normalize_text(row["Entity_Category"]),
                Rule_Basis=f"{rule_basis}; Risk basis: {risk_reason}",
            )
        )

    return pd.DataFrame([asdict(r) for r in records])


def build_risk_layer(decision_df: pd.DataFrame) -> pd.DataFrame:
    records: List[RiskRecord] = []

    for idx, row in decision_df.iterrows():
        risk_level = normalize_text(row["Risk_Level"])
        decision_type = normalize_text(row["Decision_Type"])
        confidence = parse_confidence(row["Confidence"])

        if risk_level == "LOW":
            category = "CONTROLLED"
            reason = "Signal is currently acceptable for audit trail and investor evidence pack."
        elif risk_level == "MEDIUM":
            category = "REVIEW_REQUIRED"
            reason = "Signal needs strengthening before final lender reliance."
        else:
            category = "CRITICAL_ESCALATION"
            reason = "Signal affects bankability, legal enforceability, ESG eligibility or financial close readiness."

        records.append(
            RiskRecord(
                Risk_ID=f"RISK-{idx+1:05d}",
                Signal_Reference=normalize_text(row["Signal_Reference"]),
                Risk_Category=category,
                Risk_Level=risk_level,
                Risk_Reason=reason,
                Mitigation_Action=mitigation_for(decision_type, risk_level),
                Confidence=round(confidence, 4),
            )
        )

    return pd.DataFrame([asdict(r) for r in records])


def build_gap_analysis(df: pd.DataFrame) -> pd.DataFrame:
    all_text = " ".join(
        df[["Entity_Category", "Canonical_Value", "Nearby_Keywords", "Strategic_Impact"]]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .tolist()
    ).lower()

    records: List[GapRecord] = []
    for idx, (area, keywords) in enumerate(CRITICAL_DOCUMENT_KEYWORDS.items(), start=1):
        evidence_hits = sum(1 for kw in keywords if kw.lower() in all_text)

        if evidence_hits >= 3:
            status = "EVIDENCE_PRESENT"
            risk = "LOW"
            action = "Keep evidence mapped in SSOT and attach source documents in lender data room."
        elif evidence_hits >= 1:
            status = "PARTIAL_EVIDENCE"
            risk = "MEDIUM"
            action = "Strengthen evidence with source document, owner, date, and formal approval status."
        else:
            status = "MISSING_OR_NOT_DETECTED"
            risk = "HIGH"
            action = "Create or locate required document and register it in SSOT before EIB/EBRD submission."

        records.append(
            GapRecord(
                Gap_ID=f"GAP-{idx:03d}",
                Required_Area=area.upper(),
                Status=status,
                Evidence_Count=evidence_hits,
                Risk_Level=risk,
                Recommended_Action=action,
            )
        )

    return pd.DataFrame([asdict(r) for r in records])


def build_executive_summary(
    signals_df: pd.DataFrame,
    decision_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    gap_df: pd.DataFrame,
) -> pd.DataFrame:
    total = len(decision_df)
    locked = int((signals_df["SSOT_Status"] == "LOCKED").sum())
    draft = int((signals_df["SSOT_Status"] == "DRAFT").sum())
    avg_conf = round(float(decision_df["Confidence"].mean()) if total else 0.0, 4)

    high_risk = int((decision_df["Risk_Level"] == "HIGH").sum())
    med_risk = int((decision_df["Risk_Level"] == "MEDIUM").sum())
    low_risk = int((decision_df["Risk_Level"] == "LOW").sum())

    missing_gaps = int((gap_df["Status"] == "MISSING_OR_NOT_DETECTED").sum())
    partial_gaps = int((gap_df["Status"] == "PARTIAL_EVIDENCE").sum())

    if total == 0:
        bankability_score = 0
    else:
        risk_penalty = (high_risk * 2.0 + med_risk * 0.75) / max(total, 1)
        gap_penalty = (missing_gaps * 6.0 + partial_gaps * 2.5)
        confidence_component = avg_conf * 100
        locked_component = (locked / max(total, 1)) * 100
        bankability_score = round(
            max(0, min(100, (0.55 * confidence_component + 0.45 * locked_component) - risk_penalty - gap_penalty)),
            2,
        )

    if bankability_score >= 80:
        readiness = "BANKABLE_WITH_STANDARD_REVIEW"
    elif bankability_score >= 65:
        readiness = "CONDITIONALLY_BANKABLE"
    elif bankability_score >= 50:
        readiness = "PRE_BANKABLE_REMEDIATION_REQUIRED"
    else:
        readiness = "NOT_BANKABLE_YET"

    rows = [
        ("ENGINE_VERSION", ENGINE_VERSION),
        ("SCHEMA_VERSION", SCHEMA_VERSION),
        ("RUN_TIMESTAMP", datetime.utcnow().isoformat(timespec="seconds") + "Z"),
        ("TOTAL_UNIQUE_SIGNALS", total),
        ("LOCKED_SIGNALS", locked),
        ("DRAFT_SIGNALS", draft),
        ("AVERAGE_CONFIDENCE", avg_conf),
        ("LOW_RISK_DECISIONS", low_risk),
        ("MEDIUM_RISK_DECISIONS", med_risk),
        ("HIGH_RISK_DECISIONS", high_risk),
        ("MISSING_CRITICAL_AREAS", missing_gaps),
        ("PARTIAL_CRITICAL_AREAS", partial_gaps),
        ("BANKABILITY_SCORE_0_100", bankability_score),
        ("READINESS_CLASSIFICATION", readiness),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def build_audit_log(input_path: Path, output_path: Path, signals_df: pd.DataFrame, decision_df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "engine": "TITAN_DECISION_ENGINE_v1",
        "engine_version": ENGINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "input_file": str(input_path),
        "output_file": str(output_path),
        "input_signal_count_after_cleaning": int(len(signals_df)),
        "decision_count": int(len(decision_df)),
        "columns_required": REQUIRED_COLUMNS,
        "methodology": {
            "classification": "Keyword-based deterministic rules mapped to CAPEX, financial bankability, legal compliance, ESG, technical feasibility, procurement readiness and risk control.",
            "risk_policy": "Conservative: DRAFT status, confidence below threshold, or adverse markers increase risk.",
            "gap_policy": "Critical lender areas are flagged as present, partial or missing based on keyword evidence.",
            "audit_policy": "No stochastic AI calls. Deterministic local execution for reproducibility.",
        },
    }


def autosize_excel_columns(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    worksheet = writer.sheets[sheet_name]
    for idx, col in enumerate(df.columns):
        max_len = max(
            [len(str(col))]
            + [len(str(v)) for v in df[col].head(500).fillna("").tolist()]
        )
        worksheet.set_column(idx, idx, min(max_len + 2, 60))


def write_outputs(
    input_path: Path,
    output_path: Path,
    audit_json_path: Path,
    signals_df: pd.DataFrame,
    decision_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    gap_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    audit_log: Dict[str, Any],
) -> None:
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        summary_df.to_excel(writer, sheet_name="04_EXECUTIVE_SUMMARY", index=False)
        decision_df.to_excel(writer, sheet_name="01_DECISION_TABLE", index=False)
        risk_df.to_excel(writer, sheet_name="02_RISK_LAYER", index=False)
        gap_df.to_excel(writer, sheet_name="03_GAP_ANALYSIS", index=False)
        pd.DataFrame([audit_log]).to_excel(writer, sheet_name="05_AUDIT_LOG", index=False)

        workbook = writer.book
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": "#1F2937",
            "font_color": "#FFFFFF",
            "border": 1,
        })
        locked_format = workbook.add_format({"bg_color": "#E8F5E9"})
        draft_format = workbook.add_format({"bg_color": "#FFF8E1"})
        high_format = workbook.add_format({"bg_color": "#FFCDD2"})
        medium_format = workbook.add_format({"bg_color": "#FFE0B2"})
        low_format = workbook.add_format({"bg_color": "#C8E6C9"})

        for sheet_name, df in {
            "04_EXECUTIVE_SUMMARY": summary_df,
            "01_DECISION_TABLE": decision_df,
            "02_RISK_LAYER": risk_df,
            "03_GAP_ANALYSIS": gap_df,
            "05_AUDIT_LOG": pd.DataFrame([audit_log]),
        }.items():
            ws = writer.sheets[sheet_name]
            for col_num, value in enumerate(df.columns.values):
                ws.write(0, col_num, value, header_format)
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, max(len(df), 1), max(len(df.columns) - 1, 0))
            autosize_excel_columns(writer, sheet_name, df)

            if "Risk_Level" in df.columns:
                risk_col = list(df.columns).index("Risk_Level")
                ws.conditional_format(1, risk_col, len(df), risk_col, {
                    "type": "text", "criteria": "containing", "value": "HIGH", "format": high_format
                })
                ws.conditional_format(1, risk_col, len(df), risk_col, {
                    "type": "text", "criteria": "containing", "value": "MEDIUM", "format": medium_format
                })
                ws.conditional_format(1, risk_col, len(df), risk_col, {
                    "type": "text", "criteria": "containing", "value": "LOW", "format": low_format
                })

            if "SSOT_Status" in df.columns:
                status_col = list(df.columns).index("SSOT_Status")
                ws.conditional_format(1, status_col, len(df), status_col, {
                    "type": "text", "criteria": "containing", "value": "LOCKED", "format": locked_format
                })
                ws.conditional_format(1, status_col, len(df), status_col, {
                    "type": "text", "criteria": "containing", "value": "DRAFT", "format": draft_format
                })

    audit_json_path.write_text(json.dumps(audit_log, indent=2, ensure_ascii=False), encoding="utf-8")


def run_engine(input_path: Path, output_path: Path, audit_json_path: Path) -> Dict[str, Any]:
    logging.info("TITAN Decision Engine v1 started")
    logging.info("Input: %s", input_path)

    signals_df = load_signals(input_path)
    decision_df = build_decision_table(signals_df)
    risk_df = build_risk_layer(decision_df)
    gap_df = build_gap_analysis(signals_df)
    summary_df = build_executive_summary(signals_df, decision_df, risk_df, gap_df)

    audit_log = build_audit_log(input_path, output_path, signals_df, decision_df)

    write_outputs(
        input_path=input_path,
        output_path=output_path,
        audit_json_path=audit_json_path,
        signals_df=signals_df,
        decision_df=decision_df,
        risk_df=risk_df,
        gap_df=gap_df,
        summary_df=summary_df,
        audit_log=audit_log,
    )

    logging.info("Output Excel: %s", output_path)
    logging.info("Audit JSON: %s", audit_json_path)
    logging.info("Completed successfully")

    return {
        "output_excel": str(output_path),
        "audit_json": str(audit_json_path),
        "summary": summary_df.to_dict(orient="records"),
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TITAN 11 Decision Intelligence Layer v1"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to SSOT signal extraction file (.xlsx/.xls/.xlsm/.csv)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output Excel file path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--audit-json",
        default=DEFAULT_AUDIT_JSON,
        help=f"Output audit JSON file path. Default: {DEFAULT_AUDIT_JSON}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        result = run_engine(
            input_path=Path(args.input),
            output_path=Path(args.output),
            audit_json_path=Path(args.audit_json),
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        logging.exception("TITAN Decision Engine failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
