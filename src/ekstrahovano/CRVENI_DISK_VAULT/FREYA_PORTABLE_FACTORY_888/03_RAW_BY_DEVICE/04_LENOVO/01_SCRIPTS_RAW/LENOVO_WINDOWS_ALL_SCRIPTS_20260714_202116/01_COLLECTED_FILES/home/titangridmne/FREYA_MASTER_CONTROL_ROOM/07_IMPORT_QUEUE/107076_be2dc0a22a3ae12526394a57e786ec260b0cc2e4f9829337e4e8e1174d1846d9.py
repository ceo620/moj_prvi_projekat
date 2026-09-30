#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN KERNEL — SCRIPT 51: MATRIX v1.2 HARD-GATE COMPILER
Execution Mode: SYSTEM_REPORT_GENERATION_NO_SSOT_LOCK_NO_LENDER_USE

Purpose:
    Generates a hard-gate-aware DOCUMENT_SIGNAL_COVERAGE_MATRIX workbook.

Critical doctrine:
    Coverage GREEN does NOT mean FINAL_LENDER_LOCKED.
    Final lock requires:
        - coverage >= 80%
        - p0_blocker_count = 0
        - evidence_status = SOURCE_ATTACHED
        - source_hash_status = VERIFIED
        - owner_decision_status = APPROVED
        - contradiction_status = CLOSED_OR_DISCLOSED
        - safe_wording_required = NO
        - ssot_lock_allowed = YES
        - lender_use_allowed = YES
        - breach_claim_allowed = NO unless separately authorized

This script:
    - creates workbook only
    - does not edit source files
    - does not sync to Monolith
    - does not approve SSOT lock
    - does not approve lender use
    - does not make breach claims
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, CellIsRule
from openpyxl.chart import BarChart, Reference


# ============================================================
# CONFIG
# ============================================================

OUTPUT_DIR = (
    r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL\VDR_ROOT\REPORTS"
    r"\SYSTEM_HARMONIZATION\MATRIX_COMPILER"
)

VERSION = "v1.2_HARD_GATE"
MODE = "SYSTEM_REPORT_GENERATION_NO_SSOT_LOCK_NO_LENDER_USE"
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
FILENAME = f"DOCUMENT_SIGNAL_COVERAGE_MATRIX_TITAN_{VERSION}_{TIMESTAMP}.xlsx"
MANIFEST_NAME = f"DOCUMENT_SIGNAL_COVERAGE_MATRIX_TITAN_{VERSION}_{TIMESTAMP}.json"

# Colors
NAVY = "1F4E78"
WHITE = "FFFFFF"
LIGHT_BLUE = "D9EAF7"
GREEN = "C6EFCE"
GREEN_TEXT = "006100"
AMBER = "FFF2CC"
AMBER_TEXT = "9C6500"
RED = "FFC7CE"
RED_TEXT = "9C0006"
GREY = "D9E1F2"
BLACK = "000000"

FILL_HEADER = PatternFill(start_color=NAVY, end_color=NAVY, fill_type="solid")
FONT_HEADER = Font(color=WHITE, bold=True)
FONT_TITLE = Font(color=NAVY, bold=True, size=14)
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)
THIN_BORDER = Border(
    left=Side(style="thin", color="B7B7B7"),
    right=Side(style="thin", color="B7B7B7"),
    top=Side(style="thin", color="B7B7B7"),
    bottom=Side(style="thin", color="B7B7B7"),
)


# ============================================================
# DATA
# ============================================================

INITIAL_MATRIX_ROWS = [
    {
        "document_name": "Investment Memorandum",
        "section_name": "CAPEX",
        "required_signal_count": 20,
        "available_signal_count": 12,
        "p0_blocker_count": 1,
        "evidence_status": "CANDIDATE",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Source attachment for 43.5M; CFO approval; CAPEX reconciliation",
        "blocked_claim_types": "FINAL_CAPEX;BREACH_CLAIM;FINAL_LENDER_USE",
        "next_signal_search": "CAPEX source file; CFO threshold policy; formula lineage for 58.5M"
    },
    {
        "document_name": "Investment Memorandum",
        "section_name": "Financing Structure",
        "required_signal_count": 15,
        "available_signal_count": 8,
        "p0_blocker_count": 1,
        "evidence_status": "MISSING",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "MIA grant official approval; disbursement schedule; collateral docs",
        "blocked_claim_types": "GRANT_APPROVED;FINAL_FINANCING;FINAL_LENDER_USE",
        "next_signal_search": "MIA grant official letter; grant conditions; bank term sheet"
    },
    {
        "document_name": "Investment Memorandum",
        "section_name": "Market Opportunity",
        "required_signal_count": 20,
        "available_signal_count": 6,
        "p0_blocker_count": 0,
        "evidence_status": "CANDIDATE",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Transformer shortage report; customer/offtake evidence; competitor benchmark",
        "blocked_claim_types": "MARKET_DEMAND_GUARANTEED",
        "next_signal_search": "European transformer market shortage 2026; Western Balkans grid investment"
    },
    {
        "document_name": "Investment Memorandum",
        "section_name": "ESG & Impact",
        "required_signal_count": 20,
        "available_signal_count": 5,
        "p0_blocker_count": 0,
        "evidence_status": "MISSING",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Environmental baseline; permits; waste handling; EBRD/EIB standards map",
        "blocked_claim_types": "ESG_READY;PERMIT_COMPLETE",
        "next_signal_search": "EBRD environmental social policy manufacturing; Montenegro industrial permits"
    },
    {
        "document_name": "Investment Memorandum",
        "section_name": "Legal & Ownership",
        "required_signal_count": 15,
        "available_signal_count": 12,
        "p0_blocker_count": 0,
        "evidence_status": "SOURCE_ATTACHED",
        "source_hash_status": "VERIFIED",
        "owner_decision_status": "APPROVED",
        "contradiction_status": "CLOSED_OR_DISCLOSED",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Updated UBO confirmation",
        "blocked_claim_types": "CAPEX_TOTAL;GRANT_APPROVED;COLLATERAL_VALUE;EBITDA;IRR;DSCR",
        "next_signal_search": "UBO update 2026; registration extract"
    },
    {
        "document_name": "Investment Memorandum",
        "section_name": "Risk & Mitigation",
        "required_signal_count": 15,
        "available_signal_count": 9,
        "p0_blocker_count": 0,
        "evidence_status": "CANDIDATE",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Sensitivity analysis CAPEX +10%; EBITDA -15%; interest-rate increase",
        "blocked_claim_types": "RISK_FULLY_MITIGATED",
        "next_signal_search": "CAPEX sensitivity; grant delay scenario; DSCR downside case"
    },
    {
        "document_name": "CAPEX Reconciliation Memo",
        "section_name": "All CAPEX values",
        "required_signal_count": 9,
        "available_signal_count": 9,
        "p0_blocker_count": 4,
        "evidence_status": "CANDIDATE",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "19.9M threshold typing; 43.5M source attachment; 58.5M formula lineage; 70.2M source resolution",
        "blocked_claim_types": "FINAL_CAPEX;BREACH_PROVEN;SSOT_LOCK;LENDER_USE",
        "next_signal_search": "CFO threshold policy; formula lineage; source attachment register"
    },
    {
        "document_name": "ESG Report",
        "section_name": "Permits & Baseline",
        "required_signal_count": 10,
        "available_signal_count": 2,
        "p0_blocker_count": 0,
        "evidence_status": "MISSING",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Environmental permits; baseline study; waste and emissions handling",
        "blocked_claim_types": "ESG_READY;PERMIT_COMPLETE",
        "next_signal_search": "Montenegro environmental permit industrial facility; EBRD PR manufacturing"
    },
    {
        "document_name": "Legal DD Pack",
        "section_name": "Corporate & UBO",
        "required_signal_count": 10,
        "available_signal_count": 9,
        "p0_blocker_count": 0,
        "evidence_status": "SOURCE_ATTACHED",
        "source_hash_status": "VERIFIED",
        "owner_decision_status": "APPROVED",
        "contradiction_status": "CLOSED_OR_DISCLOSED",
        "safe_wording_required": "NO",
        "critical_missing_evidence": "One updated UBO/registry extract pending",
        "blocked_claim_types": "FINANCIAL_CLAIMS;CAPEX;GRANT;COLLATERAL",
        "next_signal_search": "latest UBO extract; registry update"
    },
    {
        "document_name": "Market Analysis",
        "section_name": "Transformer Demand",
        "required_signal_count": 20,
        "available_signal_count": 6,
        "p0_blocker_count": 0,
        "evidence_status": "CANDIDATE",
        "source_hash_status": "PENDING",
        "owner_decision_status": "PENDING_CFO",
        "contradiction_status": "OPEN",
        "safe_wording_required": "YES",
        "critical_missing_evidence": "Official market report; customer/offtake evidence; regional import data",
        "blocked_claim_types": "DEMAND_GUARANTEED;OFFTAKE_CONFIRMED",
        "next_signal_search": "European transformer shortage report; grid investment Western Balkans"
    }
]

LOOKUPS = {
    "evidence_status": ["MISSING", "CANDIDATE", "SOURCE_ATTACHED"],
    "source_hash_status": ["PENDING", "VERIFIED"],
    "owner_decision_status": ["PENDING_CFO", "APPROVED"],
    "contradiction_status": ["OPEN", "CLOSED_OR_DISCLOSED"],
    "safe_wording_required": ["YES", "NO"],
    "yes_no": ["YES", "NO"],
    "allowed_use": [
        "INTERNAL_ONLY",
        "INVESTOR_SAFE_DRAFT_WITH_DISCLOSURE",
        "STRONG_INVESTOR_SAFE_DRAFT",
        "FINAL_LENDER_LOCKED"
    ]
}


# ============================================================
# COMPILER
# ============================================================

class MatrixCompilerV12:
    def __init__(self) -> None:
        self.wb = Workbook()
        self.ws_matrix = self.wb.active
        self.ws_matrix.title = "DOCUMENT_SIGNAL_COVERAGE_MATRIX"

        self.ws_dashboard = self.wb.create_sheet("DASHBOARD", 0)
        self.ws_gate = self.wb.create_sheet("DOCUMENT_READINESS_GATE")
        self.ws_claim = self.wb.create_sheet("CLAIM_PACKET_BUILDER")
        self.ws_queue = self.wb.create_sheet("NEXT_SIGNAL_SEARCH_QUEUE")
        self.ws_blockers = self.wb.create_sheet("CAPEX_MIA_HARD_BLOCKERS")
        self.ws_rules = self.wb.create_sheet("SIGNAL_MATURITY_RULES")
        self.ws_instructions = self.wb.create_sheet("INSTRUCTIONS_SAFE")
        self.ws_lookups = self.wb.create_sheet("LOOKUPS")

        self.matrix_headers = [
            "document_name", "section_name",
            "required_signal_count", "available_signal_count", "missing_signal_count", "coverage_percent",
            "coverage_status",
            "p0_blocker_count", "evidence_status", "source_hash_status", "owner_decision_status",
            "contradiction_status", "safe_wording_required",
            "ssot_lock_allowed", "lender_use_allowed", "breach_claim_allowed",
            "final_lock_allowed", "hard_gate_status", "allowed_use",
            "critical_missing_evidence", "blocked_claim_types", "next_signal_search"
        ]

    # ----------------------------
    # Generic styling
    # ----------------------------

    def style_header_row(self, ws, row: int = 1) -> None:
        for cell in ws[row]:
            cell.fill = FILL_HEADER
            cell.font = FONT_HEADER
            cell.alignment = ALIGN_CENTER
            cell.border = THIN_BORDER

    def style_all_cells(self, ws) -> None:
        for row in ws.iter_rows():
            for cell in row:
                cell.border = THIN_BORDER
                cell.alignment = ALIGN_LEFT
        ws.freeze_panes = "A2"

    def autosize(self, ws, min_width: int = 12, max_width: int = 45) -> None:
        for col in ws.columns:
            max_len = 0
            letter = col[0].column_letter
            for cell in col:
                value = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, len(value))
            ws.column_dimensions[letter].width = min(max(max_len + 2, min_width), max_width)

    # ----------------------------
    # Sheets
    # ----------------------------

    def setup_lookups(self) -> None:
        col = 1
        for name, values in LOOKUPS.items():
            self.ws_lookups.cell(row=1, column=col, value=name)
            self.ws_lookups.cell(row=1, column=col).fill = FILL_HEADER
            self.ws_lookups.cell(row=1, column=col).font = FONT_HEADER
            for r, val in enumerate(values, start=2):
                self.ws_lookups.cell(row=r, column=col, value=val)
            col += 1
        self.ws_lookups.sheet_state = "hidden"

    def setup_matrix(self) -> None:
        for col_num, header in enumerate(self.matrix_headers, start=1):
            cell = self.ws_matrix.cell(row=1, column=col_num, value=header)
            cell.fill = FILL_HEADER
            cell.font = FONT_HEADER
            cell.alignment = ALIGN_CENTER
            cell.border = THIN_BORDER

        for row_idx, item in enumerate(INITIAL_MATRIX_ROWS, start=2):
            self.ws_matrix.cell(row=row_idx, column=1, value=item["document_name"])
            self.ws_matrix.cell(row=row_idx, column=2, value=item["section_name"])
            self.ws_matrix.cell(row=row_idx, column=3, value=item["required_signal_count"])
            self.ws_matrix.cell(row=row_idx, column=4, value=item["available_signal_count"])

            # Formulas
            self.ws_matrix.cell(row=row_idx, column=5, value=f'=MAX(C{row_idx}-D{row_idx},0)')
            self.ws_matrix.cell(row=row_idx, column=6, value=f'=IFERROR(D{row_idx}/C{row_idx},0)')
            self.ws_matrix.cell(row=row_idx, column=6).number_format = "0%"

            self.ws_matrix.cell(row=row_idx, column=7, value=f'=IF(F{row_idx}>=0.8,"GREEN",IF(F{row_idx}>=0.5,"AMBER","RED"))')

            self.ws_matrix.cell(row=row_idx, column=8, value=item["p0_blocker_count"])
            self.ws_matrix.cell(row=row_idx, column=9, value=item["evidence_status"])
            self.ws_matrix.cell(row=row_idx, column=10, value=item["source_hash_status"])
            self.ws_matrix.cell(row=row_idx, column=11, value=item["owner_decision_status"])
            self.ws_matrix.cell(row=row_idx, column=12, value=item["contradiction_status"])
            self.ws_matrix.cell(row=row_idx, column=13, value=item["safe_wording_required"])

            # Hard-gate logic
            self.ws_matrix.cell(row=row_idx, column=14, value=(
                f'=IF(AND(H{row_idx}=0,I{row_idx}="SOURCE_ATTACHED",J{row_idx}="VERIFIED",'
                f'K{row_idx}="APPROVED",L{row_idx}="CLOSED_OR_DISCLOSED"),"YES","NO")'
            ))
            self.ws_matrix.cell(row=row_idx, column=15, value=f'=N{row_idx}')
            self.ws_matrix.cell(row=row_idx, column=16, value='NO')

            self.ws_matrix.cell(row=row_idx, column=17, value=(
                f'=IF(AND(G{row_idx}="GREEN",H{row_idx}=0,I{row_idx}="SOURCE_ATTACHED",'
                f'J{row_idx}="VERIFIED",K{row_idx}="APPROVED",L{row_idx}="CLOSED_OR_DISCLOSED",'
                f'M{row_idx}="NO"),"YES","NO")'
            ))

            self.ws_matrix.cell(row=row_idx, column=18, value=(
                f'=IF(H{row_idx}>0,"BLOCKED_P0",'
                f'IF(I{row_idx}<>"SOURCE_ATTACHED","BLOCKED_EVIDENCE",'
                f'IF(J{row_idx}<>"VERIFIED","BLOCKED_HASH",'
                f'IF(K{row_idx}<>"APPROVED","BLOCKED_OWNER",'
                f'IF(L{row_idx}<>"CLOSED_OR_DISCLOSED","BLOCKED_CONTRADICTION",'
                f'IF(M{row_idx}="YES","SAFE_WORDING_REQUIRED","GATES_CLEAR"))))))'
            ))

            self.ws_matrix.cell(row=row_idx, column=19, value=(
                f'=IF(Q{row_idx}="YES","FINAL_LENDER_LOCKED",'
                f'IF(AND(F{row_idx}>=0.8,H{row_idx}=0,I{row_idx}<>"MISSING"),"STRONG_INVESTOR_SAFE_DRAFT",'
                f'IF(F{row_idx}>=0.5,"INVESTOR_SAFE_DRAFT_WITH_DISCLOSURE","INTERNAL_ONLY")))'
            ))

            self.ws_matrix.cell(row=row_idx, column=20, value=item["critical_missing_evidence"])
            self.ws_matrix.cell(row=row_idx, column=21, value=item["blocked_claim_types"])
            self.ws_matrix.cell(row=row_idx, column=22, value=item["next_signal_search"])

        self.apply_matrix_validations()
        self.apply_conditional_formatting(self.ws_matrix, max_row=100)
        self.style_all_cells(self.ws_matrix)
        self.autosize(self.ws_matrix)

    def apply_matrix_validations(self) -> None:
        validations = [
            ("I2:I500", "LOOKUPS!$A$2:$A$4"),
            ("J2:J500", "LOOKUPS!$B$2:$B$3"),
            ("K2:K500", "LOOKUPS!$C$2:$C$3"),
            ("L2:L500", "LOOKUPS!$D$2:$D$3"),
            ("M2:M500", "LOOKUPS!$E$2:$E$3"),
        ]
        for range_ref, formula in validations:
            dv = DataValidation(type="list", formula1=formula, allow_blank=False)
            self.ws_matrix.add_data_validation(dv)
            dv.add(range_ref)

    def apply_conditional_formatting(self, ws, max_row: int = 100) -> None:
        # coverage_status column G
        ws.conditional_formatting.add(f"G2:G{max_row}", FormulaRule(formula=['G2="GREEN"'], fill=PatternFill(start_color=GREEN, end_color=GREEN, fill_type="solid"), font=Font(color=GREEN_TEXT)))
        ws.conditional_formatting.add(f"G2:G{max_row}", FormulaRule(formula=['G2="AMBER"'], fill=PatternFill(start_color=AMBER, end_color=AMBER, fill_type="solid"), font=Font(color=AMBER_TEXT)))
        ws.conditional_formatting.add(f"G2:G{max_row}", FormulaRule(formula=['G2="RED"'], fill=PatternFill(start_color=RED, end_color=RED, fill_type="solid"), font=Font(color=RED_TEXT)))

        # final_lock_allowed Q
        ws.conditional_formatting.add(f"Q2:Q{max_row}", FormulaRule(formula=['Q2="YES"'], fill=PatternFill(start_color=GREEN, end_color=GREEN, fill_type="solid"), font=Font(color=GREEN_TEXT)))
        ws.conditional_formatting.add(f"Q2:Q{max_row}", FormulaRule(formula=['Q2="NO"'], fill=PatternFill(start_color=RED, end_color=RED, fill_type="solid"), font=Font(color=RED_TEXT)))

        # hard_gate_status R
        ws.conditional_formatting.add(f"R2:R{max_row}", FormulaRule(formula=['R2="GATES_CLEAR"'], fill=PatternFill(start_color=GREEN, end_color=GREEN, fill_type="solid"), font=Font(color=GREEN_TEXT)))
        ws.conditional_formatting.add(f"R2:R{max_row}", FormulaRule(formula=['LEFT(R2,7)="BLOCKED"'], fill=PatternFill(start_color=RED, end_color=RED, fill_type="solid"), font=Font(color=RED_TEXT)))
        ws.conditional_formatting.add(f"R2:R{max_row}", FormulaRule(formula=['R2="SAFE_WORDING_REQUIRED"'], fill=PatternFill(start_color=AMBER, end_color=AMBER, fill_type="solid"), font=Font(color=AMBER_TEXT)))

    def setup_dashboard(self) -> None:
        ws = self.ws_dashboard
        ws["A1"] = "TITAN DOCUMENT SIGNAL COVERAGE MATRIX — HARD-GATE DASHBOARD"
        ws["A1"].font = Font(color=NAVY, bold=True, size=16)
        ws.merge_cells("A1:H1")

        rows = [
            ("Mode", MODE),
            ("Version", VERSION),
            ("Created", datetime.now(timezone.utc).isoformat()),
            ("Core warning", "GREEN coverage does not authorize FINAL_LENDER_LOCKED."),
            ("Rule", "Final lock requires evidence + hash + owner decision + contradiction closure + safe wording + hard gates."),
        ]
        for idx, (k, v) in enumerate(rows, start=3):
            ws.cell(row=idx, column=1, value=k).font = Font(bold=True)
            ws.cell(row=idx, column=2, value=v)

        ws["A10"] = "Metric"
        ws["B10"] = "Value"
        self.style_header_row(ws, 10)

        dashboard_metrics = [
            ("Total sections", '=COUNTA(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A2:A500)'),
            ("GREEN coverage sections", '=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!G2:G500,"GREEN")'),
            ("AMBER coverage sections", '=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!G2:G500,"AMBER")'),
            ("RED coverage sections", '=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!G2:G500,"RED")'),
            ("Final lock allowed sections", '=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!Q2:Q500,"YES")'),
            ("Hard-gate blocked sections", '=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!R2:R500,"BLOCKED*")'),
            ("Investor-safe sections", '=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!S2:S500,"*INVESTOR_SAFE*")'),
        ]

        for idx, (metric, formula) in enumerate(dashboard_metrics, start=11):
            ws.cell(row=idx, column=1, value=metric)
            ws.cell(row=idx, column=2, value=formula)

        chart = BarChart()
        chart.title = "Coverage Status Distribution"
        chart.y_axis.title = "Sections"
        chart.x_axis.title = "Status"
        data = Reference(ws, min_col=2, min_row=12, max_row=14)
        cats = Reference(ws, min_col=1, min_row=12, max_row=14)
        chart.add_data(data, titles_from_data=False)
        chart.set_categories(cats)
        chart.height = 7
        chart.width = 14
        ws.add_chart(chart, "D10")

        self.style_all_cells(ws)
        self.autosize(ws)

    def setup_readiness_gate(self) -> None:
        ws = self.ws_gate
        headers = [
            "document_name", "section_count", "green_sections", "amber_sections", "red_sections",
            "avg_coverage", "p0_total", "open_hard_gates", "investor_safe_gate",
            "final_lender_lock_gate", "readiness_comment"
        ]
        for c, h in enumerate(headers, 1):
            ws.cell(row=1, column=c, value=h)
        self.style_header_row(ws)

        documents = sorted(set(r["document_name"] for r in INITIAL_MATRIX_ROWS))
        for row_idx, doc in enumerate(documents, start=2):
            ws.cell(row=row_idx, column=1, value=doc)
            ws.cell(row=row_idx, column=2, value=f'=COUNTIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx})')
            ws.cell(row=row_idx, column=3, value=f'=COUNTIFS(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!G:G,"GREEN")')
            ws.cell(row=row_idx, column=4, value=f'=COUNTIFS(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!G:G,"AMBER")')
            ws.cell(row=row_idx, column=5, value=f'=COUNTIFS(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!G:G,"RED")')
            ws.cell(row=row_idx, column=6, value=f'=AVERAGEIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!F:F)')
            ws.cell(row=row_idx, column=6).number_format = "0%"
            ws.cell(row=row_idx, column=7, value=f'=SUMIF(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!H:H)')
            ws.cell(row=row_idx, column=8, value=f'=COUNTIFS(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!R:R,"BLOCKED*")')
            ws.cell(row=row_idx, column=9, value=f'=IF(E{row_idx}=0,"YES_WITH_DISCLOSURE","NO")')
            ws.cell(row=row_idx, column=10, value=f'=IF(AND(E{row_idx}=0,G{row_idx}=0,H{row_idx}=0,COUNTIFS(DOCUMENT_SIGNAL_COVERAGE_MATRIX!A:A,A{row_idx},DOCUMENT_SIGNAL_COVERAGE_MATRIX!Q:Q,"NO")=0),"YES","NO")')
            ws.cell(row=row_idx, column=11, value=f'=IF(J{row_idx}="YES","FINAL_LOCK_POSSIBLE",IF(I{row_idx}="YES_WITH_DISCLOSURE","INVESTOR_SAFE_DRAFT","INTERNAL_OR_REVIEW_ONLY"))')

        self.style_all_cells(ws)
        self.autosize(ws)

    def setup_claim_packet_builder(self) -> None:
        ws = self.ws_claim
        headers = [
            "claim_id", "claim_text", "claim_type", "value", "source_file", "page_sheet_cell",
            "source_hash", "maturity_score", "evidence_status", "allowed_use",
            "blocked_use", "safe_wording", "owner_decision_required", "final_status"
        ]
        for c, h in enumerate(headers, 1):
            ws.cell(row=1, column=c, value=h)
        self.style_header_row(ws)

        rows = [
            ["CP-CAPEX-001", "Total CAPEX candidate is EUR 43.5M", "CAPEX", "43500000", "", "", "", 3, "CANDIDATE", "INVESTOR_SAFE_DRAFT_WITH_DISCLOSURE", "FINAL_LENDER_LOCKED", "The current working SSOT register identifies a Total CAPEX candidate of EUR 43.5M, subject to reconciliation and CFO approval.", "YES", "OPEN"],
            ["CP-GRANT-001", "MIA grant candidate is EUR 10.2M", "GRANT", "10200000", "", "", "", 2, "MISSING", "INTERNAL_ONLY", "GRANT_APPROVED;FINAL_LENDER_USE", "The project includes a reported MIA grant component, subject to verification of approval documentation and grant terms.", "YES", "OPEN"],
            ["CP-COLL-001", "Equipment may support collateral structure", "COLLATERAL", "22000000", "", "", "", 3, "CANDIDATE", "INVESTOR_SAFE_DRAFT_WITH_DISCLOSURE", "PRIMARY_COLLATERAL_FINAL", "Equipment valued at EUR 22M has been identified as potential collateral, subject to ownership verification, valuation and security documentation.", "YES", "OPEN"],
        ]
        for r_idx, row in enumerate(rows, 2):
            for c_idx, val in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=val)

        self.style_all_cells(ws)
        self.autosize(ws)

    def setup_next_signal_queue(self) -> None:
        ws = self.ws_queue
        headers = [
            "task_id", "document_name", "section_name", "missing_signal", "why_needed",
            "best_source_type", "suggested_search_query", "priority", "owner", "status"
        ]
        for c, h in enumerate(headers, 1):
            ws.cell(row=1, column=c, value=h)
        self.style_header_row(ws)

        tasks = [
            ["NSQ-001", "Investment Memorandum", "CAPEX", "43.5M source attachment", "Required before any CAPEX final use", "Internal source / approved budget", "43.5M CAPEX source workbook sheet cell", "CRITICAL", "CFO / Finance Model Owner", "OPEN"],
            ["NSQ-002", "Investment Memorandum", "Financing", "MIA grant official approval", "Cannot say approved grant without official evidence", "Official grant decision", "MIA grant approval ARS Metal TITAN", "CRITICAL", "CFO", "OPEN"],
            ["NSQ-003", "Market Analysis", "Transformer Demand", "Transformer shortage report", "Needed to support market opportunity", "Official / bank / market report", "European transformer shortage 2026 report PDF", "HIGH", "Strategy", "OPEN"],
            ["NSQ-004", "ESG Report", "Permits & Baseline", "Environmental baseline and permits", "Needed for ESG/lender due diligence", "Official permit / EBRD E&S", "EBRD environmental social policy manufacturing Montenegro permits", "HIGH", "ESG Owner", "OPEN"],
        ]
        for r_idx, row in enumerate(tasks, 2):
            for c_idx, val in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=val)

        self.style_all_cells(ws)
        self.autosize(ws)

    def setup_hard_blockers(self) -> None:
        ws = self.ws_blockers
        headers = ["blocker_id", "claim", "current_status", "why_blocked", "required_resolution", "owner", "blocks_final_lender_lock"]
        for c, h in enumerate(headers, 1):
            ws.cell(row=1, column=c, value=h)
        self.style_header_row(ws)

        blockers = [
            ["HB-001", "19.9M threshold", "OPEN_THRESHOLD_TYPING_REQUIRED", "Threshold type is not CFO-defined", "CFO signs threshold policy", "CFO", "YES"],
            ["HB-002", "43.5M CAPEX candidate", "OPEN_SOURCE_REQUIRED", "Source attachment missing", "Attach source file/page/sheet/cell/hash", "CFO / Finance", "YES"],
            ["HB-003", "58.5M formula model", "OPEN_FORMULA_LINEAGE_REQUIRED", "Formula lineage missing", "Extract formula precedents and owner decision", "Financial Model Owner", "YES"],
            ["HB-004", "70.2M unattached value", "OPEN_BLOCKED_SOURCE_REQUIRED", "Value has no attached source", "Attach source or reject", "TITAN Data Owner", "YES"],
            ["HB-005", "MIA Grant 10.2M", "OPEN_SOURCE_REQUIRED", "Approval document not attached", "Attach grant decision and conditions", "CFO", "YES"],
            ["HB-006", "Equipment Collateral 22M", "OPEN_SOURCE_REQUIRED", "Valuation/security evidence missing", "Attach asset list, valuation, ownership and security docs", "CFO / Legal", "YES"],
        ]
        for r_idx, row in enumerate(blockers, 2):
            for c_idx, val in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=val)

        self.style_all_cells(ws)
        self.autosize(ws)

    def setup_rules(self) -> None:
        ws = self.ws_rules
        headers = ["score", "meaning", "allowed_use"]
        for c, h in enumerate(headers, 1):
            ws.cell(row=1, column=c, value=h)
        self.style_header_row(ws)

        rows = [
            [0, "Noise / error", "DO_NOT_USE"],
            [1, "Idea without proof", "WATCHLIST_ONLY"],
            [2, "Signal exists but no source", "INTERNAL_ONLY"],
            [3, "Has source but not final", "INVESTOR_SAFE_DRAFT"],
            [4, "Has source + good context", "STRONG_INVESTOR_SAFE_DRAFT"],
            [5, "Has source + hash + owner decision + no contradictions", "FINAL_LOCK_CANDIDATE"],
        ]
        for r_idx, row in enumerate(rows, 2):
            for c_idx, val in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=val)

        self.style_all_cells(ws)
        self.autosize(ws)

    def setup_instructions(self) -> None:
        ws = self.ws_instructions
        text = [
            ("Status", "INVESTOR_SAFE_DRAFT / Internal Governance Tool"),
            ("Rule 1", "GREEN coverage does not mean final lender ready."),
            ("Rule 2", "Final lender lock requires hard gates, not only signal coverage."),
            ("Rule 3", "Legal/corporate evidence cannot close CAPEX, grant, collateral, EBITDA, IRR or DSCR claims."),
            ("Rule 4", "CAPEX reconciliation remains open until CFO threshold typing, source attachment and formula lineage are resolved."),
            ("Rule 5", "Use safe wording for all unresolved claims."),
        ]
        ws["A1"] = "TITAN MATRIX SAFE INSTRUCTIONS"
        ws["A1"].font = FONT_TITLE
        ws.merge_cells("A1:B1")
        for idx, (k, v) in enumerate(text, 3):
            ws.cell(row=idx, column=1, value=k).font = Font(bold=True)
            ws.cell(row=idx, column=2, value=v)

        self.style_all_cells(ws)
        self.autosize(ws)

    def compile(self) -> Path:
        self.setup_lookups()
        self.setup_matrix()
        self.setup_dashboard()
        self.setup_readiness_gate()
        self.setup_claim_packet_builder()
        self.setup_next_signal_queue()
        self.setup_hard_blockers()
        self.setup_rules()
        self.setup_instructions()

        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        filepath = Path(OUTPUT_DIR) / FILENAME
        self.wb.save(filepath)

        manifest = {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "mode": MODE,
            "version": VERSION,
            "output": str(filepath),
            "ssot_lock_allowed": "NO",
            "lender_use_allowed": "NO",
            "breach_claim_allowed": "NO",
            "critical_rule": "Coverage GREEN does not authorize final lender lock.",
            "sheets": self.wb.sheetnames,
        }
        manifest_path = Path(OUTPUT_DIR) / MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        print("\n[+] TITAN MATRIX v1.2 HARD-GATE generated.")
        print(f"[+] Workbook: {filepath}")
        print(f"[+] Manifest: {manifest_path}")
        print("[+] Mode: SYSTEM_REPORT_GENERATION_NO_SSOT_LOCK_NO_LENDER_USE")
        print("[+] Final lender lock: NO")
        print("[+] Breach claim: NO\n")

        return filepath


if __name__ == "__main__":
    compiler = MatrixCompilerV12()
    compiler.compile()
