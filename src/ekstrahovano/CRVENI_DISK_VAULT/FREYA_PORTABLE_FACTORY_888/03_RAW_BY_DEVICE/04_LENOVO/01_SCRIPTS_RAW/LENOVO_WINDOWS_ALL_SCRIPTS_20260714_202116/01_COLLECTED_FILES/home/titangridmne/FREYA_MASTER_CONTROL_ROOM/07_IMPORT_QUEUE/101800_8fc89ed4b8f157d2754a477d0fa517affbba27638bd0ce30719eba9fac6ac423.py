#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py

TITAN 11 - Forensic Signal Validation Engine v3.4 AUDIT LOCKED
Purpose:
    Performs forensic validation of TITAN document signals and produces
    audit-grade risk, conflict, and SSOT-readiness outputs.

Inputs supported:
    1) SQLite database with table document_signals
    2) Excel / CSV / JSON signal export from 14_check_document_signals.py

Outputs:
    - TITAN_FORENSIC_REPORT_v3_4.xlsx
    - TITAN_FORENSIC_REPORT_v3_4.json
    - TITAN_FORENSIC_CONFLICTS_v3_4.csv
    - forensic_engine_manifest_v3_4.json
    - forensic_engine_audit_log_v3_4.jsonl

Core logic:
    - POA validation
    - LOCKED / DRAFT validation
    - duplicate signal detection
    - conflict detection by Entity_Category
    - risk scoring
    - SSOT readiness classification
    - EIB/EBRD lender-readiness interpretation

Usage:
    python TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py --db-path "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS\\03_ORCHESTRATION\\v29_state.db" --output-dir "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS\\04_KERNEL\\forensic_reports"

    python TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py --input "document_signals_v1.xlsx" --output-dir "./forensic_reports"

    python TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py --db-path ./database/sqlite/titan_state.db --strict
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import platform
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except ImportError:
    pd = None


SCRIPT_NAME = "TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py"
SCRIPT_VERSION = "3.4"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"
FORENSIC_SCHEMA_VERSION = "TITAN_FORENSIC_SCHEMA_v3_4"
DEFAULT_ROOT = "TITAN_11"
DEFAULT_DB_RELATIVE = "database/sqlite/titan_state.db"
DEFAULT_OUTPUT_RELATIVE = "exports/forensic"


EXPECTED_SIGNAL_COLUMNS = [
    "Signal_ID",
    "Entity_Category",
    "Canonical_Value",
    "Confidence_Score_POA",
    "Nearby_Keywords",
    "SSOT_Status",
    "Strategic_Impact",
]

ALT_COLUMN_MAP = {
    "signal_id": "Signal_ID",
    "Signal_ID": "Signal_ID",
    "Document_ID": "Document_ID",
    "document_id": "Document_ID",
    "entity_category": "Entity_Category",
    "Entity_Category": "Entity_Category",
    "canonical_value": "Canonical_Value",
    "Canonical_Value": "Canonical_Value",
    "confidence_score": "Confidence_Score_POA",
    "Confidence_Score_POA": "Confidence_Score_POA",
    "Confidence_Score (POA)": "Confidence_Score_POA",
    "nearby_keywords": "Nearby_Keywords",
    "Nearby_Keywords": "Nearby_Keywords",
    "ssot_status": "SSOT_Status",
    "SSOT_Status": "SSOT_Status",
    "strategic_impact": "Strategic_Impact",
    "Strategic_Impact": "Strategic_Impact",
    "source_reference": "Source_Path",
    "Source_Path": "Source_Path",
    "file_name": "File_Name",
    "File_Name": "File_Name",
    "Signal_Code": "Signal_Code",
}


CRITICAL_CATEGORIES = {
    "FINANCING",
    "FINANCIAL_COVENANT",
    "CAPEX",
    "LEGAL_PERMIT",
    "LEGAL_CONTRACT",
    "LEGAL_OWNERSHIP",
    "ESG",
    "TECHNICAL_GRID",
    "PROCUREMENT",
    "RISK",
}


LENDER_CRITICAL_KEYWORDS = [
    "loan", "debt", "dscr", "capex", "permit", "license", "ownership",
    "land", "esia", "eia", "ebrd", "eib", "ifc", "contract", "grid",
    "procurement", "risk", "sensitivity", "covenant", "collateral",
    "kredit", "dozvola", "ugovor", "vlasnist", "vlasništ", "zemljište"
]


@dataclass
class ForensicEvent:
    timestamp_utc: str
    event_type: str
    object_name: str
    status: str
    details: str


@dataclass
class ForensicFinding:
    Finding_ID: str
    Signal_ID: str
    Document_ID: str
    Entity_Category: str
    Canonical_Value: str
    POA: float
    SSOT_Status: str
    Forensic_Status: str
    Risk_Level: str
    Finding_Type: str
    Finding_Reason: str
    Recommended_Action: str
    Strategic_Impact: str


@dataclass
class ConflictRecord:
    Conflict_ID: str
    Entity_Category: str
    Canonical_Value_A: str
    Canonical_Value_B: str
    Signal_A: str
    Signal_B: str
    Conflict_Type: str
    Severity: str
    Resolution_Action: str


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def resolve_base_dir(base_dir: Optional[str]) -> Path:
    if base_dir:
        return Path(base_dir).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if cwd.name == DEFAULT_ROOT:
        return cwd
    if (cwd / DEFAULT_ROOT).exists():
        return (cwd / DEFAULT_ROOT).resolve()
    return cwd / DEFAULT_ROOT


def resolve_db_path(base_dir: Path, db_path: Optional[str]) -> Path:
    if db_path:
        return Path(db_path).expanduser().resolve()
    env_db = os.environ.get("TITAN_DB_PATH")
    if env_db:
        p = Path(env_db).expanduser()
        return (base_dir / p).resolve() if not p.is_absolute() else p.resolve()
    return (base_dir / DEFAULT_DB_RELATIVE).resolve()


def resolve_output_dir(base_dir: Path, output_dir: Optional[str]) -> Path:
    if output_dir:
        return Path(output_dir).expanduser().resolve()
    return (base_dir / DEFAULT_OUTPUT_RELATIVE).resolve()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd is not None and pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def normalize_key(value: Any) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_poa(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        if pd is not None and pd.isna(value):
            return 0.0
    except Exception:
        pass
    text = str(value).replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0.0
    number = float(match.group(1))
    if number > 1:
        number /= 100.0
    return round(max(0.0, min(1.0, number)), 4)


def normalize_status(value: Any) -> str:
    text = normalize_text(value).upper()
    if "LOCKED" in text:
        return "LOCKED"
    if "DRAFT" in text:
        return "DRAFT"
    return "DRAFT"


def read_json_records(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["records", "signals", "data"]:
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("JSON file must contain a list or a dict with records/signals/data list.")


def load_input_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    suffix = path.suffix.lower()

    if suffix == ".json":
        return read_json_records(path)

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    if suffix in {".xlsx", ".xlsm", ".xls"}:
        if pd is None:
            raise ImportError("pandas/openpyxl required for Excel input.")
        workbook = pd.ExcelFile(path)
        preferred = "01_DOCUMENT_SIGNALS" if "01_DOCUMENT_SIGNALS" in workbook.sheet_names else workbook.sheet_names[0]
        df = pd.read_excel(path, sheet_name=preferred)
        df.columns = [str(c).strip() for c in df.columns]
        return df.to_dict(orient="records")

    raise ValueError("Unsupported input format. Use .json, .csv, .xlsx, .xlsm or .xls")


class TitanForensicEngine:
    def __init__(
        self,
        base_dir: Path,
        output_dir: Path,
        db_path: Optional[Path] = None,
        input_file: Optional[Path] = None,
        strict: bool = False,
        min_locked_poa: float = 0.80,
        min_draft_poa: float = 0.50,
    ) -> None:
        self.base_dir = base_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.db_path = db_path.resolve() if db_path else None
        self.input_file = input_file.resolve() if input_file else None
        self.strict = strict
        self.min_locked_poa = min_locked_poa
        self.min_draft_poa = min_draft_poa
        self.events: List[ForensicEvent] = []

    def event(self, event_type: str, object_name: str, status: str, details: str) -> None:
        self.events.append(ForensicEvent(utc_now(), event_type, object_name, status, details))

    def prepare(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs" / "audit").mkdir(parents=True, exist_ok=True)

        if self.input_file:
            if not self.input_file.exists():
                raise FileNotFoundError(f"Input file not found: {self.input_file}")
            self.event("filesystem", str(self.input_file), "ready", "Signal input file exists.")

        if self.db_path:
            if not self.db_path.exists():
                raise FileNotFoundError(f"SQLite database not found: {self.db_path}")
            self.event("filesystem", str(self.db_path), "ready", "SQLite database exists.")

        if not self.input_file and not self.db_path:
            raise ValueError("Provide either --input or --db-path.")

        self.event("filesystem", str(self.output_dir), "ready", "Output directory ready.")

    def load_from_db(self) -> List[Dict[str, Any]]:
        assert self.db_path is not None
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT
                    signal_id AS Signal_ID,
                    document_id AS Document_ID,
                    entity_category AS Entity_Category,
                    canonical_value AS Canonical_Value,
                    confidence_score AS Confidence_Score_POA,
                    nearby_keywords AS Nearby_Keywords,
                    ssot_status AS SSOT_Status,
                    strategic_impact AS Strategic_Impact,
                    source_reference AS Source_Path,
                    metadata_json AS Metadata_JSON
                FROM document_signals
                ORDER BY signal_id;
                """
            ).fetchall()
            records = [dict(row) for row in rows]
            self.event("load_db", str(self.db_path), "loaded", f"Signals loaded from DB: {len(records)}")
            return records
        finally:
            conn.close()

    def load_signals(self) -> List[Dict[str, Any]]:
        if self.input_file:
            records = load_input_file(self.input_file)
            self.event("load_file", str(self.input_file), "loaded", f"Signals loaded from file: {len(records)}")
        else:
            records = self.load_from_db()

        normalized = []
        for record in records:
            out: Dict[str, Any] = {}
            for k, v in record.items():
                mapped = ALT_COLUMN_MAP.get(str(k).strip(), str(k).strip())
                out[mapped] = v

            out["Signal_ID"] = normalize_text(out.get("Signal_ID"))
            out["Document_ID"] = normalize_text(out.get("Document_ID"))
            out["Entity_Category"] = normalize_text(out.get("Entity_Category")).upper()
            out["Canonical_Value"] = normalize_text(out.get("Canonical_Value"))
            out["Confidence_Score_POA"] = parse_poa(out.get("Confidence_Score_POA"))
            out["Nearby_Keywords"] = normalize_text(out.get("Nearby_Keywords"))
            out["SSOT_Status"] = normalize_status(out.get("SSOT_Status"))
            out["Strategic_Impact"] = normalize_text(out.get("Strategic_Impact"))
            out["Source_Path"] = normalize_text(out.get("Source_Path"))
            out["File_Name"] = normalize_text(out.get("File_Name"))
            normalized.append(out)

        self.event("normalize", "signals", "completed", f"Normalized signals: {len(normalized)}")
        return normalized

    def assess_signal(self, record: Dict[str, Any], duplicate_count: int) -> ForensicFinding:
        signal_id = normalize_text(record.get("Signal_ID"))
        document_id = normalize_text(record.get("Document_ID"))
        category = normalize_text(record.get("Entity_Category")).upper()
        value = normalize_text(record.get("Canonical_Value"))
        poa = parse_poa(record.get("Confidence_Score_POA"))
        status = normalize_status(record.get("SSOT_Status"))
        impact = normalize_text(record.get("Strategic_Impact"))
        nearby = normalize_text(record.get("Nearby_Keywords"))

        reasons: List[str] = []
        finding_types: List[str] = []

        if not signal_id:
            reasons.append("missing_signal_id")
            finding_types.append("SCHEMA_DEFECT")

        if not category:
            reasons.append("missing_entity_category")
            finding_types.append("SCHEMA_DEFECT")

        if not value:
            reasons.append("missing_canonical_value")
            finding_types.append("SCHEMA_DEFECT")

        if poa <= 0:
            reasons.append("missing_or_invalid_poa")
            finding_types.append("POA_DEFECT")

        if status == "LOCKED" and poa < self.min_locked_poa:
            reasons.append(f"locked_signal_below_poa_threshold_{self.min_locked_poa}")
            finding_types.append("LOCK_INTEGRITY_DEFECT")

        if status == "DRAFT" and poa < self.min_draft_poa:
            reasons.append(f"draft_signal_below_poa_threshold_{self.min_draft_poa}")
            finding_types.append("LOW_EVIDENCE_SIGNAL")

        if duplicate_count > 1:
            reasons.append(f"duplicate_signal_key_count_{duplicate_count}")
            finding_types.append("DUPLICATE_SIGNAL")

        combined = normalize_key(" ".join([category, value, nearby, impact]))
        lender_critical = category in CRITICAL_CATEGORIES or any(k in combined for k in LENDER_CRITICAL_KEYWORDS)

        if lender_critical and status != "LOCKED":
            reasons.append("lender_critical_signal_not_locked")
            finding_types.append("BANKABILITY_REVIEW")

        if lender_critical and poa < 0.75:
            reasons.append("lender_critical_signal_low_poa")
            finding_types.append("BANKABILITY_REVIEW")

        if not reasons:
            forensic_status = "VALIDATED"
            risk_level = "LOW"
            finding_type = "CONTROLLED"
            finding_reason = "Signal passes forensic validation thresholds."
            action = "Keep in SSOT and include as supporting evidence where relevant."
        else:
            finding_type = "|".join(sorted(set(finding_types)))
            finding_reason = "; ".join(reasons)

            if "SCHEMA_DEFECT" in finding_types or "LOCK_INTEGRITY_DEFECT" in finding_types:
                risk_level = "HIGH"
                forensic_status = "REJECT_OR_REWORK"
                action = "Correct source schema/value, rerun extraction and do not rely on this signal until remediated."
            elif lender_critical:
                risk_level = "HIGH" if poa < 0.65 else "MEDIUM"
                forensic_status = "ESCALATE"
                action = "Attach stronger evidence, source document, owner and approval trail before lender package."
            elif poa < 0.50:
                risk_level = "MEDIUM"
                forensic_status = "REVIEW_REQUIRED"
                action = "Reclassify or strengthen extraction basis."
            else:
                risk_level = "MEDIUM"
                forensic_status = "REVIEW_REQUIRED"
                action = "Analyst review required before SSOT lock."

        return ForensicFinding(
            Finding_ID="",
            Signal_ID=signal_id,
            Document_ID=document_id,
            Entity_Category=category,
            Canonical_Value=value,
            POA=poa,
            SSOT_Status=status,
            Forensic_Status=forensic_status,
            Risk_Level=risk_level,
            Finding_Type=finding_type,
            Finding_Reason=finding_reason,
            Recommended_Action=action,
            Strategic_Impact=impact,
        )

    def detect_conflicts(self, records: List[Dict[str, Any]]) -> List[ConflictRecord]:
        conflicts: List[ConflictRecord] = []
        by_category: Dict[str, List[Dict[str, Any]]] = {}

        for r in records:
            category = normalize_text(r.get("Entity_Category")).upper()
            value = normalize_key(r.get("Canonical_Value"))
            if not category or not value:
                continue
            by_category.setdefault(category, []).append(r)

        counter = 1
        for category, group in by_category.items():
            # Only detect conflicts where same category has materially different values.
            unique_values: Dict[str, Dict[str, Any]] = {}
            for r in group:
                key = normalize_key(r.get("Canonical_Value"))
                if key:
                    unique_values.setdefault(key, r)

            if len(unique_values) <= 1:
                continue

            # Conservative conflict detection for critical categories only.
            if category not in CRITICAL_CATEGORIES:
                continue

            values = list(unique_values.items())
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    value_a, rec_a = values[i]
                    value_b, rec_b = values[j]

                    # Avoid flagging generic repeated category labels unless materially distinct.
                    if value_a in value_b or value_b in value_a:
                        continue

                    poa_a = parse_poa(rec_a.get("Confidence_Score_POA"))
                    poa_b = parse_poa(rec_b.get("Confidence_Score_POA"))

                    if poa_a >= 0.70 and poa_b >= 0.70:
                        severity = "HIGH"
                    else:
                        severity = "MEDIUM"

                    conflicts.append(
                        ConflictRecord(
                            Conflict_ID=f"CONF-{counter:05d}",
                            Entity_Category=category,
                            Canonical_Value_A=normalize_text(rec_a.get("Canonical_Value")),
                            Canonical_Value_B=normalize_text(rec_b.get("Canonical_Value")),
                            Signal_A=normalize_text(rec_a.get("Signal_ID")),
                            Signal_B=normalize_text(rec_b.get("Signal_ID")),
                            Conflict_Type="MULTIPLE_CANONICAL_VALUES_IN_CRITICAL_CATEGORY",
                            Severity=severity,
                            Resolution_Action="Resolve via SSOT arbitration: source authority, date, document owner and POA comparison.",
                        )
                    )
                    counter += 1

                    # Prevent combinatorial explosion.
                    if counter > 1000:
                        self.event("conflict_detection", category, "truncated", "Conflict output capped at 1000.")
                        return conflicts

        self.event("conflict_detection", "records", "completed", f"Conflicts detected: {len(conflicts)}")
        return conflicts

    def run_validation(self, records: List[Dict[str, Any]]) -> Tuple[List[ForensicFinding], List[ConflictRecord]]:
        key_counts: Dict[str, int] = {}
        for r in records:
            key = normalize_key(f"{r.get('Entity_Category')}||{r.get('Canonical_Value')}")
            if key:
                key_counts[key] = key_counts.get(key, 0) + 1

        findings: List[ForensicFinding] = []
        for idx, r in enumerate(records, start=1):
            key = normalize_key(f"{r.get('Entity_Category')}||{r.get('Canonical_Value')}")
            finding = self.assess_signal(r, key_counts.get(key, 1))
            finding.Finding_ID = f"FND-{idx:05d}"
            findings.append(finding)

        conflicts = self.detect_conflicts(records)

        # Upgrade findings linked to conflict records.
        conflict_signal_ids = set()
        for c in conflicts:
            conflict_signal_ids.add(c.Signal_A)
            conflict_signal_ids.add(c.Signal_B)

        for f in findings:
            if f.Signal_ID in conflict_signal_ids:
                if f.Risk_Level == "LOW":
                    f.Risk_Level = "MEDIUM"
                f.Forensic_Status = "CONFLICT_REVIEW"
                if "CONFLICT" not in f.Finding_Type:
                    f.Finding_Type = f.Finding_Type + "|CONFLICT" if f.Finding_Type else "CONFLICT"
                f.Finding_Reason += "; linked_to_conflict_registry"
                f.Recommended_Action = "Resolve conflict through TITAN Arbiter before SSOT lock."

        self.event("validation", "signals", "completed", f"Findings created: {len(findings)}")
        return findings, conflicts

    def build_summary(self, records: List[Dict[str, Any]], findings: List[ForensicFinding], conflicts: List[ConflictRecord]) -> Dict[str, Any]:
        total = len(findings)
        validated = sum(1 for f in findings if f.Forensic_Status == "VALIDATED")
        high = sum(1 for f in findings if f.Risk_Level == "HIGH")
        medium = sum(1 for f in findings if f.Risk_Level == "MEDIUM")
        low = sum(1 for f in findings if f.Risk_Level == "LOW")
        locked = sum(1 for f in findings if f.SSOT_Status == "LOCKED")
        draft = sum(1 for f in findings if f.SSOT_Status == "DRAFT")
        avg_poa = round(sum(f.POA for f in findings) / total, 4) if total else 0.0

        if total == 0:
            readiness_score = 0.0
        else:
            validation_component = (validated / total) * 100
            locked_component = (locked / total) * 100
            poa_component = avg_poa * 100
            risk_penalty = high * 1.8 + medium * 0.6 + len(conflicts) * 2.5
            readiness_score = round(max(0, min(100, validation_component * 0.35 + locked_component * 0.30 + poa_component * 0.35 - risk_penalty)), 2)

        if readiness_score >= 85 and high == 0 and len(conflicts) == 0:
            readiness = "AUDIT_LOCKED"
        elif readiness_score >= 70:
            readiness = "CONDITIONALLY_LOCKABLE"
        elif readiness_score >= 50:
            readiness = "REMEDIATION_REQUIRED"
        else:
            readiness = "NOT_READY_FOR_LENDER_RELIANCE"

        return {
            "system_name": SYSTEM_NAME,
            "script_name": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "schema_version": FORENSIC_SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "total_input_signals": len(records),
            "total_findings": total,
            "validated_findings": validated,
            "locked_signals": locked,
            "draft_signals": draft,
            "low_risk": low,
            "medium_risk": medium,
            "high_risk": high,
            "conflict_count": len(conflicts),
            "average_poa": avg_poa,
            "forensic_readiness_score_0_100": readiness_score,
            "forensic_readiness_class": readiness,
            "strict_mode": self.strict,
            "min_locked_poa": self.min_locked_poa,
            "min_draft_poa": self.min_draft_poa,
        }

    def export_outputs(
        self,
        records: List[Dict[str, Any]],
        findings: List[ForensicFinding],
        conflicts: List[ConflictRecord],
        summary: Dict[str, Any],
    ) -> Dict[str, str]:
        findings_records = [asdict(f) for f in findings]
        conflicts_records = [asdict(c) for c in conflicts]

        xlsx_path = self.output_dir / "TITAN_FORENSIC_REPORT_v3_4.xlsx"
        json_path = self.output_dir / "TITAN_FORENSIC_REPORT_v3_4.json"
        conflicts_csv_path = self.output_dir / "TITAN_FORENSIC_CONFLICTS_v3_4.csv"

        json_path.write_text(
            json.dumps(
                {"summary": summary, "findings": findings_records, "conflicts": conflicts_records},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        with conflicts_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            fieldnames = list(conflicts_records[0].keys()) if conflicts_records else [field.name for field in ConflictRecord.__dataclass_fields__.values()]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(conflicts_records)

        if pd is not None:
            findings_df = pd.DataFrame(findings_records)
            conflicts_df = pd.DataFrame(conflicts_records)
            summary_df = pd.DataFrame(summary.items(), columns=["Metric", "Value"])
            input_df = pd.DataFrame(records)

            with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
                summary_df.to_excel(writer, sheet_name="00_EXECUTIVE_SUMMARY", index=False)
                findings_df.to_excel(writer, sheet_name="01_FORENSIC_FINDINGS", index=False)
                conflicts_df.to_excel(writer, sheet_name="02_CONFLICTS", index=False)
                input_df.to_excel(writer, sheet_name="03_INPUT_SIGNALS", index=False)

                workbook = writer.book
                header_format = workbook.add_format({
                    "bold": True,
                    "bg_color": "#111827",
                    "font_color": "#FFFFFF",
                    "border": 1,
                })
                high_format = workbook.add_format({"bg_color": "#F8D7DA"})
                medium_format = workbook.add_format({"bg_color": "#FFF3CD"})
                low_format = workbook.add_format({"bg_color": "#D1E7DD"})
                locked_format = workbook.add_format({"bg_color": "#E8F5E9"})
                draft_format = workbook.add_format({"bg_color": "#FFF8E1"})

                sheets = {
                    "00_EXECUTIVE_SUMMARY": summary_df,
                    "01_FORENSIC_FINDINGS": findings_df,
                    "02_CONFLICTS": conflicts_df,
                    "03_INPUT_SIGNALS": input_df,
                }

                for sheet_name, df in sheets.items():
                    ws = writer.sheets[sheet_name]
                    for col_num, value in enumerate(df.columns.values):
                        ws.write(0, col_num, value, header_format)
                    ws.freeze_panes(1, 0)
                    if len(df.columns) > 0:
                        ws.autofilter(0, 0, max(len(df), 1), len(df.columns) - 1)
                    for idx, col in enumerate(df.columns):
                        if df.empty:
                            max_len = len(str(col))
                        else:
                            max_len = max([len(str(col))] + [len(str(v)) for v in df[col].head(500).fillna("").tolist()])
                        ws.set_column(idx, idx, min(max_len + 2, 70))

                if not findings_df.empty and "Risk_Level" in findings_df.columns:
                    ws = writer.sheets["01_FORENSIC_FINDINGS"]
                    col = list(findings_df.columns).index("Risk_Level")
                    ws.conditional_format(1, col, len(findings_df), col, {"type": "text", "criteria": "containing", "value": "HIGH", "format": high_format})
                    ws.conditional_format(1, col, len(findings_df), col, {"type": "text", "criteria": "containing", "value": "MEDIUM", "format": medium_format})
                    ws.conditional_format(1, col, len(findings_df), col, {"type": "text", "criteria": "containing", "value": "LOW", "format": low_format})

                if not findings_df.empty and "SSOT_Status" in findings_df.columns:
                    ws = writer.sheets["01_FORENSIC_FINDINGS"]
                    col = list(findings_df.columns).index("SSOT_Status")
                    ws.conditional_format(1, col, len(findings_df), col, {"type": "text", "criteria": "containing", "value": "LOCKED", "format": locked_format})
                    ws.conditional_format(1, col, len(findings_df), col, {"type": "text", "criteria": "containing", "value": "DRAFT", "format": draft_format})

                if not conflicts_df.empty and "Severity" in conflicts_df.columns:
                    ws = writer.sheets["02_CONFLICTS"]
                    col = list(conflicts_df.columns).index("Severity")
                    ws.conditional_format(1, col, len(conflicts_df), col, {"type": "text", "criteria": "containing", "value": "HIGH", "format": high_format})
                    ws.conditional_format(1, col, len(conflicts_df), col, {"type": "text", "criteria": "containing", "value": "MEDIUM", "format": medium_format})
        else:
            xlsx_path = Path("")

        self.event("export", str(self.output_dir), "completed", "Forensic outputs exported.")
        return {
            "excel": str(xlsx_path) if str(xlsx_path) else "",
            "json": str(json_path),
            "conflicts_csv": str(conflicts_csv_path),
        }

    def write_manifest_and_audit(self, summary: Dict[str, Any], outputs: Dict[str, str]) -> Dict[str, Any]:
        manifest = {
            "system_name": SYSTEM_NAME,
            "script_name": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "schema_version": FORENSIC_SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "python_version": sys.version,
            "platform": platform.platform(),
            "base_dir": str(self.base_dir),
            "db_path": str(self.db_path) if self.db_path else "",
            "input_file": str(self.input_file) if self.input_file else "",
            "output_dir": str(self.output_dir),
            "summary": summary,
            "outputs": outputs,
            "methodology": {
                "validation": "deterministic forensic rules",
                "poa_policy": "LOCKED requires high POA; DRAFT below threshold is review signal",
                "conflict_policy": "critical categories with materially different canonical values are conflict candidates",
                "lender_policy": "critical EIB/EBRD categories require LOCKED status or escalation",
                "strict_mode": self.strict,
                "source_mutation": "none for file input; optional DB read only in this engine",
            },
            "next_phase": {
                "script": "05_kernel_decision_engine.py or TITAN_ARBITER_v1.py",
                "purpose": "Resolve conflicts and convert validated evidence into final decisions.",
            },
        }

        manifest_path = self.output_dir / "forensic_engine_manifest_v3_4.json"
        audit_path = self.output_dir / "forensic_engine_audit_log_v3_4.jsonl"

        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        with audit_path.open("w", encoding="utf-8") as f:
            for event in self.events:
                f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

        central_audit = self.base_dir / "logs" / "audit" / "forensic_engine_audit_log_v3_4.jsonl"
        try:
            central_audit.parent.mkdir(parents=True, exist_ok=True)
            central_audit.write_text(audit_path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass

        return manifest

    def run(self) -> Dict[str, Any]:
        logging.info("TITAN Forensic Engine v3.4 started")
        self.prepare()
        records = self.load_signals()
        findings, conflicts = self.run_validation(records)
        summary = self.build_summary(records, findings, conflicts)
        outputs = self.export_outputs(records, findings, conflicts, summary)
        manifest = self.write_manifest_and_audit(summary, outputs)

        if self.strict and summary["high_risk"] > 0:
            self.event("strict_mode", "high_risk", "failed", "Strict mode detected high-risk findings.")

        logging.info("Forensic Engine completed. Readiness: %s", summary["forensic_readiness_class"])
        return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN Forensic Engine v3.4 AUDIT LOCKED.")
    parser.add_argument("--base-dir", default=None, help=f"TITAN root directory. Default: ./{DEFAULT_ROOT} or current TITAN_11 directory.")
    parser.add_argument("--db-path", default=None, help="SQLite database path containing document_signals.")
    parser.add_argument("--input", default=None, help="Signal export file: .xlsx, .csv or .json.")
    parser.add_argument("--output-dir", default=None, help="Output directory for forensic reports.")
    parser.add_argument("--strict", action="store_true", help="Strict mode: high-risk findings produce non-zero exit.")
    parser.add_argument("--min-locked-poa", type=float, default=0.80, help="Minimum POA for LOCKED signal. Default: 0.80.")
    parser.add_argument("--min-draft-poa", type=float, default=0.50, help="Minimum POA for DRAFT signal. Default: 0.50.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    try:
        base_dir = resolve_base_dir(args.base_dir)
        output_dir = resolve_output_dir(base_dir, args.output_dir)

        db_path = resolve_db_path(base_dir, args.db_path) if args.db_path else None
        input_file = Path(args.input).expanduser().resolve() if args.input else None

        if not db_path and not input_file:
            # Default to base-dir DB if explicit input not provided.
            db_path = resolve_db_path(base_dir, None)

        engine = TitanForensicEngine(
            base_dir=base_dir,
            output_dir=output_dir,
            db_path=db_path,
            input_file=input_file,
            strict=args.strict,
            min_locked_poa=args.min_locked_poa,
            min_draft_poa=args.min_draft_poa,
        )

        manifest = engine.run()
        print(json.dumps(manifest["summary"], indent=2, ensure_ascii=False))
        print("\nTITAN forensic validation completed.")
        print(f"Excel: {manifest['outputs']['excel']}")
        print(f"JSON: {manifest['outputs']['json']}")

        if args.strict and manifest["summary"]["high_risk"] > 0:
            return 2

        return 0

    except Exception as exc:
        logging.exception("TITAN forensic engine failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
