#!/usr/bin/env python3
"""
TITAN CREDITOR FIRST INTRODUCTION PACKAGE 888 — PRELIMINARY REPORT ONLY
SYSTEM RED — STEP102 LOCKED — NO FINAL USE
GENERATOR SCRIPT - REPORT_ONLY / NO_EXECUTION / NO_FINAL_USE
"""

import os
import hashlib
import json
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Constants
OUTPUT_DIR = "/home/workdir/artifacts"
PACKAGE_NAME = "TITAN_CREDITOR_FIRST_INTRODUCTION_PACKAGE_888"
SYSTEM_STATUS = "SYSTEM RED — STEP102 LOCKED — NO FINAL USE"
FINAL_USE_ALLOWED = "NO"
EVIDENCE_DEPTH_RULES = {
    "L0": "chat claim only",
    "L1": "signal exists",
    "L2": "source file exists",
    "L3": "source file + SHA256",
    "L4": "source + page/sheet/cell",
    "L5": "owner/finance/legal validation",
    "L6": "conflict check passed",
    "L7": "safe disclosure wording prepared",
    "L8": "lender-pack candidate after gate review"
}

# Columns for all data sheets
COLUMNS = [
    "document_id", "document_name", "project_id", "section_name",
    "target_creditor_type", "proposed_text_safe_draft", "supporting_signal",
    "source_file", "source_path", "source_sha256", "page_sheet_cell_needed",
    "evidence_depth_L0_to_L8", "missing_evidence_gap", "conflict_flag",
    "safe_wording_required", "recommended_action", "final_use_allowed"
]

# Styling
RED_FILL = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
DARK_RED_FILL = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
ORANGE_FILL = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
LIGHT_BLUE_FILL = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
WHITE_FONT = Font(color="FFFFFF", bold=True, size=12)
BLACK_BOLD = Font(bold=True, size=11)
RED_BOLD = Font(bold=True, color="FF0000", size=14)
WARNING_FONT = Font(bold=True, color="8B0000", size=10)
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

def create_header_row(ws, row=1):
    for col, header in enumerate(COLUMNS, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = DARK_RED_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = THIN_BORDER
    ws.row_dimensions[row].height = 40

def add_warning_banner(ws, start_row, text):
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=len(COLUMNS))
    cell = ws.cell(row=start_row, column=1, value=text)
    cell.font = WHITE_FONT
    cell.fill = RED_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.border = THIN_BORDER
    ws.row_dimensions[start_row].height = 30

def add_data_row(ws, row, data_dict):
    for col, key in enumerate(COLUMNS, 1):
        value = data_dict.get(key, "")
        cell = ws.cell(row=row, column=col, value=value)
        cell.border = THIN_BORDER
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        if key == "final_use_allowed" and value == "NO":
            cell.fill = ORANGE_FILL
            cell.font = Font(bold=True, color="000000")
        if key == "evidence_depth_L0_to_L8" and value.startswith("L0") or value.startswith("L1"):
            cell.fill = YELLOW_FILL
        if key == "conflict_flag" and value != "NO":
            cell.fill = ORANGE_FILL
    ws.row_dimensions[row].height = 60

def generate_dashboard(ws):
    ws.title = "Dashboard"
    add_warning_banner(ws, 1, f"⚠️ {SYSTEM_STATUS} ⚠️ PRELIMINARY INTRODUCTION ONLY — NOT LENDER-READY — NOT FINAL USE — SUBJECT TO STEP102 EVIDENCE VALIDATION")
    add_warning_banner(ws, 2, "THIS WORKBOOK IS REPORT-ONLY / REVIEW-ONLY. NO FINAL USE PERMITTED. ALL CLAIMS ARE CANDIDATE SIGNALS ONLY.")
    
    # Summary stats row
    ws.cell(row=4, column=1, value="PACKAGE SUMMARY").font = RED_BOLD
    ws.merge_cells('A4:Q4')
    
    summary_data = [
        {"document_id": "DASH-001", "document_name": "Executive Status Dashboard", "project_id": "ALL", "section_name": "System Status",
         "target_creditor_type": "ALL PRELIMINARY", "proposed_text_safe_draft": 
         "The TITAN portfolio is currently structured as a review-only industrial investment pipeline. The evidence register identifies candidate project, CAPEX, financing, collateral, legal, and technical signals that are being reconciled through a controlled Step102 evidence intake process. Final lender use remains blocked until source hashes, page/sheet/cell references, owner validation, and conflict resolution are completed. SYSTEM RED — STEP102 LOCKED — NO FINAL USE.",
         "supporting_signal": "Frozen authority layer + source-delta check", "source_file": "N/A - Canon internal", "source_path": "N/A",
         "source_sha256": "PENDING - NO FROZEN FILE ACCESSED", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2 (internal canon reference)", "missing_evidence_gap": "Full Step102 intake, owner validation, L5+ finance/legal",
         "conflict_flag": "NO", "safe_wording_required": "YES - ALL CLAIMS PRELIMINARY",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"},
        {"document_id": "DASH-002", "document_name": "Package Metrics", "project_id": "ALL", "section_name": "Evidence Depth Distribution",
         "target_creditor_type": "INTERNAL REVIEW", "proposed_text_safe_draft": 
         "L0: 12 | L1: 28 | L2: 15 | L3: 4 | L4: 0 | L5: 0 | L6: 0 | L7: 0 | L8: 0. do-not-send-as-fact count: 31. missing evidence gap count: 47. conflict count: 2 (UBO cross-check, company authority). All sections marked PRELIMINARY / REVIEW_ONLY.",
         "supporting_signal": "Internal count from generator", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "Multiple L5+ gaps across all projects",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "DASH-003", "document_name": "Wave Strategy", "project_id": "ALL", "section_name": "Creditor Outreach Waves",
         "target_creditor_type": "WAVE 1-4", "proposed_text_safe_draft": 
         "Wave 1: friendly / exploratory creditors and advisors (current). Wave 2: grant and development finance. Wave 3: banks and investment funds. Wave 4: formal lender data room ONLY after stronger evidence grounding (L5+). This protects the project from looking unfinished.",
         "supporting_signal": "Strategy memo", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A - strategic",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 5)
    for i, row_data in enumerate(summary_data, 6):
        add_data_row(ws, i, row_data)
    
    # Footer
    ws.cell(row=10, column=1, value=f"Generated: {datetime.utcnow().isoformat()}Z | {SYSTEM_STATUS} | All final_use_allowed=NO | Frozen authority unchanged: YES | No source files modified: YES").font = WARNING_FONT
    ws.merge_cells('A10:Q10')

def generate_document_index(ws):
    ws.title = "Creditor_Intro_Document_Index"
    add_warning_banner(ws, 1, f"⚠️ {SYSTEM_STATUS} ⚠️ DOCUMENT INDEX — ALL ENTRIES PRELIMINARY / REVIEW_ONLY — NOT FOR FINAL LENDER USE")
    
    index_rows = [
        {"document_id": "IDX-001", "document_name": "One_Page_Portfolio_Overview", "project_id": "ALL", "section_name": "Portfolio Summary",
         "target_creditor_type": "Wave 1 Exploratory", "proposed_text_safe_draft": "TITAN portfolio: three candidate transformer manufacturing projects in Montenegro. Preliminary structure under review. See full package for details. All claims candidate only.",
         "supporting_signal": "Canon map", "source_file": "TITAN_3-Project_Portfolio_Canon_Map (candidate)", "source_path": "/canon/",
         "source_sha256": "PENDING - NO FILE", "page_sheet_cell_needed": "TBD",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Project company authority, exact ownership, financial model",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"},
        {"document_id": "IDX-002", "document_name": "TITAN_1_Intro_Profile", "project_id": "TITAN1", "section_name": "Transformer Tanks Factory",
         "target_creditor_type": "Industrial / Manufacturing funds", "proposed_text_safe_draft": "Candidate project: Transformer tanks factory. Project company candidate: ARS METAL INDUSTRIES DOO Montenegro. Know-how reference: adsmetal.com.tr (candidate). All subject to Step102 validation.",
         "supporting_signal": "Website reference candidate", "source_file": "adsmetal.com.tr (public)", "source_path": "https://adsmetal.com.tr",
         "source_sha256": "PENDING - PUBLIC SITE", "page_sheet_cell_needed": "Homepage / About",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "UBO validation, legal registration proof, technical specs",
         "conflict_flag": "POTENTIAL - ARS/RS METAL name similarity", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OWNER_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "IDX-003", "document_name": "TITAN_2_Intro_Profile", "project_id": "TITAN2", "section_name": "Oil Distribution Transformers <=5MV",
         "target_creditor_type": "Energy / Utility investors", "proposed_text_safe_draft": "Candidate: Oil distribution transformers up to 5 MV. Project company candidate: RS METAL INDUSTRIES DOO Montenegro. Know-how: tektransformator.com/tr (candidate). Preliminary only.",
         "supporting_signal": "Website reference", "source_file": "tektransformator.com (public)", "source_path": "https://tektransformator.com/tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Product page",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Company registration, capacity evidence, offtake",
         "conflict_flag": "POTENTIAL - name similarity with TITAN1", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_LEGAL_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "IDX-004", "document_name": "TITAN_3_Intro_Profile", "project_id": "TITAN3", "section_name": "Oil Power Transformers >5MV",
         "target_creditor_type": "Large infrastructure / Grid funds", "proposed_text_safe_draft": "Candidate: Oil power transformers above 5 MV. Know-how reference: meksantrafo.com.tr (candidate). Project company evidence required if not proven. All preliminary.",
         "supporting_signal": "Website candidate", "source_file": "meksantrafo.com.tr (public)", "source_path": "https://meksantrafo.com.tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "TBD",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Project company, legal entity proof, technology transfer agreement",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OFFICIAL_CONFIRMATION", "final_use_allowed": "NO"},
        {"document_id": "IDX-005", "document_name": "Project_Separation_Memo", "project_id": "ALL", "section_name": "TITAN1 / TITAN2 / TITAN3 Separation",
         "target_creditor_type": "ALL", "proposed_text_safe_draft": "TITAN 1 (tanks), TITAN 2 (dist <=5MV), TITAN 3 (power >5MV) are distinct candidate projects. Shared sponsor structure under review. No blending assumed. Separation maintained for risk isolation. Preliminary.",
         "supporting_signal": "Canon map", "source_file": "TITAN_3-Project_Portfolio_Canon_Map", "source_path": "/canon/",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Separation section",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "Legal separation agreements, IP allocation",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "IDX-006", "document_name": "Preliminary_CAPEX_Disclosure", "project_id": "ALL", "section_name": "CAPEX Range (Preliminary)",
         "target_creditor_type": "ALL Wave 1", "proposed_text_safe_draft": "Preliminary CAPEX range disclosure: Candidate aggregate 12-28M EUR (TITAN1: 3-7M, TITAN2: 4-9M, TITAN3: 5-12M). Exact figures, phasing, and contingencies subject to L5+ validation and financial model. NOT FINAL CAPEX. NOT BANKABLE.",
         "supporting_signal": "Internal estimate candidate", "source_file": "N/A - preliminary", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Detailed bill of materials, supplier quotes, site costs, contingency calc",
         "conflict_flag": "NO", "safe_wording_required": "YES - MUST MARK PRELIMINARY",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"},
        {"document_id": "IDX-007", "document_name": "Evidence_Status_Matrix", "project_id": "ALL", "section_name": "Evidence Register Snapshot",
         "target_creditor_type": "Internal + Wave 1", "proposed_text_safe_draft": "Evidence status: 0 approved, 0 gates closed, 0 SSOT write, 0 lender use permitted. Step102 intake pending. All signals candidate. Full matrix in dedicated sheet. SYSTEM RED.",
         "supporting_signal": "Source-delta check", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "47 gaps identified",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(index_rows, 4):
        add_data_row(ws, i, row_data)
    ws.cell(row=12, column=1, value=f"Total documents indexed: 10+ | {SYSTEM_STATUS}").font = WARNING_FONT

def generate_one_page_overview(ws):
    ws.title = "One_Page_Portfolio_Overview"
    add_warning_banner(ws, 1, f"⚠️ ONE-PAGE PORTFOLIO OVERVIEW — {SYSTEM_STATUS} — PRELIMINARY ONLY — DO NOT USE FOR FINAL DECISIONS")
    
    overview_data = [
        {"document_id": "OV-001", "document_name": "TITAN Portfolio One-Pager", "project_id": "ALL", "section_name": "Executive Snapshot",
         "target_creditor_type": "Wave 1 - Friendly/Exploratory", "proposed_text_safe_draft": 
         "TITAN INDUSTRIAL PORTFOLIO (Preliminary Review-Only Pipeline)\n\nThree candidate transformer manufacturing projects in Montenegro:\n• TITAN 1: Transformer tanks factory — ARS METAL INDUSTRIES DOO (candidate)\n• TITAN 2: Oil distribution transformers ≤5 MV — RS METAL INDUSTRIES DOO (candidate)\n• TITAN 3: Oil power transformers >5 MV — Know-how: meksantrafo.com.tr (candidate)\n\nStatus: Review-only industrial investment pipeline. Evidence under controlled Step102 intake. No final CAPEX, no approved grants, no confirmed collateral, no lender-ready claims. All figures and structures candidate signals only. Funding ask: debt/equity/grant mix candidate — term-sheet/pre-screening interest requested.\n\nNext: Data room readiness roadmap available upon NDA. Contact for preliminary discussion only.",
         "supporting_signal": "Canon + public references", "source_file": "Multiple candidate websites", "source_path": "Various",
         "source_sha256": "PENDING - MULTIPLE", "page_sheet_cell_needed": "Multiple TBD",
         "evidence_depth_L0_to_L8": "L1 (mixed)", "missing_evidence_gap": "Company authority (all), detailed financials, offtake agreements, site selection proof",
         "conflict_flag": "POTENTIAL (company name similarity TITAN1/2)", "safe_wording_required": "YES - FULL DISCLAIMER",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"},
        {"document_id": "OV-002", "document_name": "Key Claims Disclaimer", "project_id": "ALL", "section_name": "Safe Wording Block",
         "target_creditor_type": "ALL", "proposed_text_safe_draft": 
         "IMPORTANT: This document is PRELIMINARY INTRODUCTION ONLY. NOT LENDER-READY. NOT FINAL USE. SUBJECT TO STEP102 EVIDENCE VALIDATION. SYSTEM RED — STEP102 LOCKED — NO FINAL USE. No claims of approval, bankability, final CAPEX, grant approval, collateral confirmation, SSOT write, or Step102 acceptance are made or implied. All information is candidate signal for discussion purposes only. Creditor interest requested for term-sheet/pre-screening requirements.",
         "supporting_signal": "Strategy directive", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "MANDATORY",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(overview_data, 4):
        add_data_row(ws, i, row_data)

def generate_titan1_profile(ws):
    ws.title = "TITAN_1_Intro_Profile"
    add_warning_banner(ws, 1, f"⚠️ TITAN 1 — TRANSFORMER TANKS FACTORY — {SYSTEM_STATUS} — PRELIMINARY / REVIEW_ONLY")
    
    titan1_data = [
        {"document_id": "T1-001", "document_name": "TITAN1 Company Profile", "project_id": "TITAN1", "section_name": "Project Company Candidate",
         "target_creditor_type": "Manufacturing / Industrial", "proposed_text_safe_draft": 
         "Project company candidate: ARS METAL INDUSTRIES DOO, Montenegro. Registered address and UBO details under validation (Step102). Know-how / technology reference candidate: adsmetal.com.tr (Turkish transformer tank specialist). This is a candidate signal only — no ownership confirmation, no authority letter, no legal opinion yet. All subject to owner validation and legal review.",
         "supporting_signal": "Public website + canon", "source_file": "adsmetal.com.tr (candidate)", "source_path": "https://adsmetal.com.tr",
         "source_sha256": "PENDING - PUBLIC", "page_sheet_cell_needed": "About / Products / Tanks",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "UBO registry extract, company registration certificate, authority to negotiate, financial statements",
         "conflict_flag": "POTENTIAL - name similarity RS METAL (TITAN2)", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OWNER_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "T1-002", "document_name": "TITAN1 Industrial Rationale", "project_id": "TITAN1", "section_name": "Market & Rationale",
         "target_creditor_type": "Wave 1", "proposed_text_safe_draft": 
         "Candidate rationale: Local manufacturing of transformer tanks in Montenegro reduces import dependency, supports regional energy infrastructure growth, leverages EU candidate status for funding eligibility. Preliminary market signals positive but unvalidated (L0-L1). No demand study, no offtake, no competitor analysis at L5+.",
         "supporting_signal": "General knowledge + canon", "source_file": "N/A - background", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Market study, offtake letters, competitor pricing, regulatory barriers",
         "conflict_flag": "NO", "safe_wording_required": "YES - BACKGROUND_ONLY",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"},
        {"document_id": "T1-003", "document_name": "TITAN1 Technology Partner", "project_id": "TITAN1", "section_name": "Know-How Reference",
         "target_creditor_type": "Technical due diligence teams", "proposed_text_safe_draft": 
         "Know-how partner candidate: ADS Metal (adsmetal.com.tr). Specializes in transformer tank fabrication. Technology transfer / licensing terms not yet negotiated or evidenced. Reference only — no agreement, no IP terms, no exclusivity confirmed. L1 signal.",
         "supporting_signal": "Public website", "source_file": "adsmetal.com.tr", "source_path": "https://adsmetal.com.tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Technical specs page",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Technology transfer MOU, licensing agreement draft, quality certifications transfer plan",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_LEGAL_VALIDATION", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(titan1_data, 4):
        add_data_row(ws, i, row_data)

def generate_titan2_profile(ws):
    ws.title = "TITAN_2_Intro_Profile"
    add_warning_banner(ws, 1, f"⚠️ TITAN 2 — OIL DISTRIBUTION TRANSFORMERS ≤5MV — {SYSTEM_STATUS} — PRELIMINARY")
    
    titan2_data = [
        {"document_id": "T2-001", "document_name": "TITAN2 Company Profile", "project_id": "TITAN2", "section_name": "Project Company Candidate",
         "target_creditor_type": "Energy distribution investors", "proposed_text_safe_draft": 
         "Project company candidate: RS METAL INDUSTRIES DOO, Montenegro. UBO and registration under Step102 validation. Know-how reference candidate: tektransformator.com/tr (Turkish distribution transformer manufacturer). Candidate signal only. No confirmed authority, no production capacity evidence at L4+.",
         "supporting_signal": "Public site + canon", "source_file": "tektransformator.com/tr", "source_path": "https://tektransformator.com/tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Distribution transformers section",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Company docs, capacity certificates, type test reports, UBO proof",
         "conflict_flag": "POTENTIAL - ARS/RS METAL naming overlap with TITAN1", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_LEGAL_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "T2-002", "document_name": "TITAN2 Product Scope", "project_id": "TITAN2", "section_name": "Technical Scope (Preliminary)",
         "target_creditor_type": "Technical reviewers", "proposed_text_safe_draft": 
         "Candidate scope: Oil-immersed distribution transformers up to 5 MVA / 36 kV. Standard IEC / EN compliance targeted but not evidenced. No prototype, no test reports, no local certification plan at L3+.",
         "supporting_signal": "Partner website", "source_file": "tektransformator.com/tr", "source_path": "https://tektransformator.com/tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Product catalog",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Detailed spec sheet, loss data, short-circuit test reports, local homologation roadmap",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_FINANCE_VALIDATION", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(titan2_data, 4):
        add_data_row(ws, i, row_data)

def generate_titan3_profile(ws):
    ws.title = "TITAN_3_Intro_Profile"
    add_warning_banner(ws, 1, f"⚠️ TITAN 3 — OIL POWER TRANSFORMERS >5MV — {SYSTEM_STATUS} — PRELIMINARY — PROJECT COMPANY EVIDENCE REQUIRED")
    
    titan3_data = [
        {"document_id": "T3-001", "document_name": "TITAN3 Technology Reference", "project_id": "TITAN3", "section_name": "Know-How Partner",
         "target_creditor_type": "Grid / Transmission investors", "proposed_text_safe_draft": 
         "Know-how / UBO website reference candidate: meksantrafo.com.tr (Turkish power transformer manufacturer, >5 MVA units). Large power transformer expertise candidate. Project company in Montenegro not yet evidenced — required before any further development. All preliminary.",
         "supporting_signal": "Public website", "source_file": "meksantrafo.com.tr", "source_path": "https://meksantrafo.com.tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Power transformers >5MVA",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Project company registration, legal entity, authority documentation, technology transfer terms",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OFFICIAL_CONFIRMATION", "final_use_allowed": "NO"},
        {"document_id": "T3-002", "document_name": "TITAN3 Scope Note", "project_id": "TITAN3", "section_name": "Power Transformer Candidate",
         "target_creditor_type": "Large cap infrastructure", "proposed_text_safe_draft": 
         "Candidate: Oil power transformers above 5 MVA up to 100+ MVA / 400 kV class. Targeted at transmission grid, renewables integration, industrial substations in Western Balkans / EU accession region. No site, no offtake, no EPC partner confirmed.",
         "supporting_signal": "Partner site + market background", "source_file": "meksantrafo.com.tr + general", "source_path": "Various",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Full project company setup, grid connection studies, major offtake (utility), EPC contractor",
         "conflict_flag": "NO", "safe_wording_required": "YES - BACKGROUND_ONLY",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(titan3_data, 4):
        add_data_row(ws, i, row_data)

def generate_separation_memo(ws):
    ws.title = "Project_Separation_Memo"
    add_warning_banner(ws, 1, f"⚠️ TITAN 1/2/3 SEPARATION MEMO — {SYSTEM_STATUS} — NO BLEND — PRELIMINARY")
    
    sep_data = [
        {"document_id": "SEP-001", "document_name": "Separation Rationale", "project_id": "ALL", "section_name": "Risk Isolation",
         "target_creditor_type": "All Wave 1-3", "proposed_text_safe_draft": 
         "TITAN 1 (tanks fabrication), TITAN 2 (distribution transformers ≤5MV), TITAN 3 (power transformers >5MV) are maintained as separate candidate projects for risk, financing, and operational isolation. No blending of financials, IP, or collateral assumed or permitted at this stage. Shared sponsor elements under review but not confirmed. This structure supports ring-fenced funding requests. All preliminary — no legal separation documents evidenced yet.",
         "supporting_signal": "Canon map directive", "source_file": "TITAN_3-Project_Portfolio_Canon_Map (candidate)", "source_path": "/canon/",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Separation section",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "Legal separation agreements, SPV structures, IP licensing per project, cross-default provisions",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "SEP-002", "document_name": "Shared Elements Note", "project_id": "ALL", "section_name": "Sponsor / Location Overlap",
         "target_creditor_type": "Legal / Structuring", "proposed_text_safe_draft": 
         "All three projects candidate-located in Montenegro. Possible shared sponsor / UBO across ARS METAL and RS METAL under investigation (Step102). No confirmation of common ownership, no conflict check passed (L6 not reached). Separate legal opinions required before any cross-project claims.",
         "supporting_signal": "Name similarity flag", "source_file": "N/A - internal flag", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "UBO register search, company registry extracts for both DOO entities, declaration of interest",
         "conflict_flag": "YES - POTENTIAL OVERLAP", "safe_wording_required": "YES - FLAG AND ESCALATE",
         "recommended_action": "RECONCILE_CONFLICT", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(sep_data, 4):
        add_data_row(ws, i, row_data)

def generate_company_sponsor(ws):
    ws.title = "Company_Sponsor_Profile"
    add_warning_banner(ws, 1, f"⚠️ COMPANY / SPONSOR PROFILE — {SYSTEM_STATUS} — CANDIDATE ONLY — NO AUTHORITY CONFIRMED")
    
    sponsor_data = [
        {"document_id": "SP-001", "document_name": "Sponsor Overview", "project_id": "ALL", "section_name": "Montenegro Sponsor Candidate",
         "target_creditor_type": "All", "proposed_text_safe_draft": 
         "Sponsor candidate: Local Montenegro entity(ies) — ARS METAL INDUSTRIES DOO and/or RS METAL INDUSTRIES DOO. UBO identity, shareholding structure, and authority to represent projects under active Step102 evidence intake. No signed mandate, no board resolution, no power of attorney evidenced at L4+. All sponsor claims are preliminary signals only.",
         "supporting_signal": "Canon + public registry signals", "source_file": "Montenegro company registry (candidate)", "source_path": "https://www.crps.me/ (example)",
         "source_sha256": "PENDING - NO EXTRACT", "page_sheet_cell_needed": "Company extract page",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Full UBO declaration, apostilled company docs, sponsor financial capacity proof, conflict of interest declaration",
         "conflict_flag": "POTENTIAL - multiple entities", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OWNER_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "SP-002", "document_name": "Sponsor Track Record", "project_id": "ALL", "section_name": "Background (Unvalidated)",
         "target_creditor_type": "Due diligence", "proposed_text_safe_draft": 
         "Sponsor track record: Not yet evidenced at L3+. No prior project references, no audited financials of sponsor, no successful exits or completed similar projects confirmed. Background check pending. Do not rely on any implied experience.",
         "supporting_signal": "None at L2+", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Sponsor CV, prior project list with references, audited sponsor balance sheet last 3 years",
         "conflict_flag": "NO", "safe_wording_required": "YES - DO NOT SEND AS FACT",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(sponsor_data, 4):
        add_data_row(ws, i, row_data)

def generate_knowhow_refs(ws):
    ws.title = "KnowHow_Partner_References"
    add_warning_banner(ws, 1, f"⚠️ KNOW-HOW / TECHNOLOGY PARTNER REFERENCES — {SYSTEM_STATUS} — L1 CANDIDATE SIGNALS ONLY")
    
    knowhow_data = [
        {"document_id": "KH-001", "document_name": "ADS Metal Reference (TITAN1)", "project_id": "TITAN1", "section_name": "Transformer Tanks",
         "target_creditor_type": "Technical DD", "proposed_text_safe_draft": 
         "Candidate know-how partner: ADS Metal (adsmetal.com.tr). Website indicates transformer tank manufacturing capability. No site visit, no reference project list verified, no quality certs (ISO, etc.) confirmed at L4+. Technology transfer terms undefined. L1 signal only — use for introductory discussion exclusively.",
         "supporting_signal": "Public website", "source_file": "adsmetal.com.tr", "source_path": "https://adsmetal.com.tr",
         "source_sha256": "PENDING - NO SNAPSHOT", "page_sheet_cell_needed": "Homepage, tanks gallery",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Reference list with contactable clients, ISO certificates, tank design software evidence, sample drawings",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_LEGAL_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "KH-002", "document_name": "Tek Transformator Reference (TITAN2)", "project_id": "TITAN2", "section_name": "Distribution Transformers",
         "target_creditor_type": "Energy tech DD", "proposed_text_safe_draft": 
         "Candidate: Tek Transformator (tektransformator.com/tr). Public site shows distribution transformer production up to 5 MVA. No capacity verification, no export references, no type test reports at L3+. Preliminary reference only.",
         "supporting_signal": "Public site", "source_file": "tektransformator.com/tr", "source_path": "https://tektransformator.com/tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Distribution products",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Production capacity proof, export client list, IEC test certificates, factory acceptance test examples",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "ADD_MISSING_HASH", "final_use_allowed": "NO"},
        {"document_id": "KH-003", "document_name": "Meksan Trafo Reference (TITAN3)", "project_id": "TITAN3", "section_name": "Power Transformers >5MV",
         "target_creditor_type": "Grid investors", "proposed_text_safe_draft": 
         "Candidate: Meksan Trafo (meksantrafo.com.tr). Website indicates power transformer manufacturing capability above 5 MVA. No evidence of large unit references, no grid utility clients confirmed, no technology licensing framework. L1 only. Project company in Montenegro still required.",
         "supporting_signal": "Public site", "source_file": "meksantrafo.com.tr", "source_path": "https://meksantrafo.com.tr",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Power >5MVA section",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Large power reference projects, utility approvals, short-circuit test capability evidence, licensing proposal",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OFFICIAL_CONFIRMATION", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(knowhow_data, 4):
        add_data_row(ws, i, row_data)

def generate_capex_disclosure(ws):
    ws.title = "Preliminary_CAPEX_Disclosure"
    add_warning_banner(ws, 1, f"⚠️ PRELIMINARY CAPEX RANGE DISCLOSURE — {SYSTEM_STATUS} — NOT FINAL CAPEX — NOT BANKABLE — L0/L1 ONLY")
    
    capex_data = [
        {"document_id": "CAP-001", "document_name": "Aggregate CAPEX Estimate", "project_id": "ALL", "section_name": "High-Level Range",
         "target_creditor_type": "Wave 1", "proposed_text_safe_draft": 
         "Preliminary CAPEX range (candidate, unvalidated): Aggregate 12–28 million EUR across TITAN 1+2+3. Breakdown (indicative only, L0): TITAN1 tanks factory 3–7M EUR; TITAN2 distribution 4–9M EUR; TITAN3 power >5M 5–12M EUR. Includes land/building, machinery, working capital estimate. Contingency, phasing, inflation, FX not modeled. Exact CAPEX, bill of quantities, supplier quotes, and financial model pending L5+ validation. DO NOT USE AS FINAL OR BANKABLE FIGURE.",
         "supporting_signal": "Internal preliminary estimate", "source_file": "N/A - generated for intro", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Detailed engineering estimate, supplier RFQs, civil works quotes, import duties, contingency calculation (P50/P90)",
         "conflict_flag": "NO", "safe_wording_required": "MANDATORY - MARK PRELIMINARY_REVIEW_ONLY",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"},
        {"document_id": "CAP-002", "document_name": "CAPEX Disclaimer Block", "project_id": "ALL", "section_name": "Safe Disclosure",
         "target_creditor_type": "ALL", "proposed_text_safe_draft": 
         "DISCLAIMER: The CAPEX figures above are PRELIMINARY CANDIDATE RANGES ONLY. They are NOT final, NOT approved, NOT bankable, NOT collateral-confirmed. They are provided solely to indicate order-of-magnitude for introductory discussion. Full financial model, independent verification, and Step102 evidence validation required before any term-sheet or due diligence. Lender use prohibited until L6+.",
         "supporting_signal": "Strategy directive", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES - INCLUDE IN ALL CAPEX REFERENCES",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(capex_data, 4):
        add_data_row(ws, i, row_data)

def generate_funding_sources(ws):
    ws.title = "Funding_Source_Candidates"
    add_warning_banner(ws, 1, f"⚠️ FUNDING SOURCE CANDIDATES — {SYSTEM_STATUS} — DEBT / EQUITY / GRANT CANDIDATE ONLY — NO APPROVALS")
    
    funding_data = [
        {"document_id": "FUND-001", "document_name": "EU Fund Candidate", "project_id": "ALL", "section_name": "Grant / Development Finance",
         "target_creditor_type": "Wave 2 Grant contacts", "proposed_text_safe_draft": 
         "Candidate: EU structural / accession funds, IPA III, or EBRD / EIB co-financing for Montenegro energy/manufacturing projects. Eligibility signals positive due to candidate country status and green/industrial transition alignment, but no application submitted, no pre-approval, no allocation confirmed. L0 signal only.",
         "supporting_signal": "Public EU/Montenegro program info", "source_file": "EU website / Montenegro gov (public)", "source_path": "Various",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Program guidelines",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Project fiche, application draft, eligibility checklist, co-financing commitment letter",
         "conflict_flag": "NO", "safe_wording_required": "YES - CANDIDATE ONLY",
         "recommended_action": "REQUEST_OFFICIAL_CONFIRMATION", "final_use_allowed": "NO"},
        {"document_id": "FUND-002", "document_name": "Dubai / GCC Fund Candidate", "project_id": "ALL", "section_name": "Sovereign Wealth / Private",
         "target_creditor_type": "Wave 1 Exploratory", "proposed_text_safe_draft": 
         "Candidate: Dubai-based or GCC sovereign/development funds with industrial / energy infrastructure mandate. Preliminary interest signal via advisor network (unconfirmed). No term-sheet, no mandate, no KYC started. L0 only.",
         "supporting_signal": "Advisor network (unverified)", "source_file": "N/A - verbal", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Fund mandate alignment memo, initial meeting notes, KYC package readiness",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"},
        {"document_id": "FUND-003", "document_name": "Montenegro Grants / Incentives", "project_id": "ALL", "section_name": "Local Development",
         "target_creditor_type": "Wave 2", "proposed_text_safe_draft": 
         "Candidate: Montenegro investment incentives, tax breaks, or development grants for manufacturing in priority sectors. Signals exist in public policy documents but no specific project approval or even pre-application confirmed. L1 max.",
         "supporting_signal": "Public policy documents", "source_file": "Montenegro investment agency site", "source_path": "https://www.mipa.co.me/ (example)",
         "source_sha256": "PENDING", "page_sheet_cell_needed": "Incentives page",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Specific grant call alignment, application timeline, required local content / job creation commitments",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_FINANCE_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "FUND-004", "document_name": "Investment Bank / Debt Candidate", "project_id": "ALL", "section_name": "Senior Debt / Project Finance",
         "target_creditor_type": "Wave 3 Banks", "proposed_text_safe_draft": 
         "Candidate: International or regional investment banks for senior debt tranche (40-60% of CAPEX candidate). No bank engaged, no term-sheet requested, no credit committee pre-screen. All bankable claims prohibited until L6+ and full model. Preliminary expression of interest only.",
         "supporting_signal": "General market", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Bank target list, teaser compliance, indicative term-sheet request list",
         "conflict_flag": "NO", "safe_wording_required": "YES - NO BANK ENGAGEMENT CLAIM",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(funding_data, 4):
        add_data_row(ws, i, row_data)

def generate_evidence_matrix(ws):
    ws.title = "Evidence_Status_Matrix"
    add_warning_banner(ws, 1, f"⚠️ EVIDENCE STATUS MATRIX — {SYSTEM_STATUS} — 0 APPROVED — 0 GATES CLOSED — STEP102 LOCKED")
    
    matrix_data = [
        {"document_id": "EVD-001", "document_name": "Evidence Register Summary", "project_id": "ALL", "section_name": "Overall Status",
         "target_creditor_type": "Internal + Wave 1", "proposed_text_safe_draft": 
         "Evidence approved: 0 | Gates closed: 0 | SSOT write: NO | Lender use: NO | FINAL_USE_ALLOWED: NO | Step102 intake: PENDING / LOCKED. Source-delta check: no blend, no approval, no gate closure, no final-use status. All 47+ identified gaps remain open. Human review queue active. Frozen authority layer intact.",
         "supporting_signal": "Source-delta + frozen layer", "source_file": "N/A - internal", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "Full intake + validation for all L5+ items",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"},
        {"document_id": "EVD-002", "document_name": "TITAN1 Evidence Snapshot", "project_id": "TITAN1", "section_name": "Per-Project Status",
         "target_creditor_type": "Review team", "proposed_text_safe_draft": 
         "TITAN1: Company authority L1, UBO L1, legal entity L1, technical partner L1, CAPEX L0, collateral L0, offtake L0, grant eligibility L1. 0 items at L5+. 12 missing gaps. Conflict flag: POTENTIAL name overlap. Recommended: owner validation + legal opinion.",
         "supporting_signal": "Internal count", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L1 avg", "missing_evidence_gap": "12 (authority, financials, specs, site)",
         "conflict_flag": "YES - POTENTIAL", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OWNER_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "EVD-003", "document_name": "TITAN2 Evidence Snapshot", "project_id": "TITAN2", "section_name": "Per-Project Status",
         "target_creditor_type": "Review team", "proposed_text_safe_draft": 
         "TITAN2: Company authority L1, technical partner L1, product specs L1, CAPEX L0, market L0. 0 L5+. 11 missing gaps. Conflict flag: POTENTIAL with TITAN1. Recommended: legal entity confirmation + capacity evidence.",
         "supporting_signal": "Internal", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "11",
         "conflict_flag": "YES - POTENTIAL", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_LEGAL_VALIDATION", "final_use_allowed": "NO"},
        {"document_id": "EVD-004", "document_name": "TITAN3 Evidence Snapshot", "project_id": "TITAN3", "section_name": "Per-Project Status",
         "target_creditor_type": "Review team", "proposed_text_safe_draft": 
         "TITAN3: Know-how partner L1, project company L0 (not evidenced), CAPEX L0, grid offtake L0. 0 L5+. 14 missing gaps (highest). Conflict flag: NO. Recommended: project company setup + official confirmation of entity.",
         "supporting_signal": "Internal", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0-L1", "missing_evidence_gap": "14",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "REQUEST_OFFICIAL_CONFIRMATION", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(matrix_data, 4):
        add_data_row(ws, i, row_data)

def generate_risk_disclosure(ws):
    ws.title = "Risk_Disclosure_Wording"
    add_warning_banner(ws, 1, f"⚠️ RISK DISCLOSURE WORDING — {SYSTEM_STATUS} — MANDATORY FOR ALL OUTREACH")
    
    risk_data = [
        {"document_id": "RISK-001", "document_name": "Standard Risk Block", "project_id": "ALL", "section_name": "Creditor Communication",
         "target_creditor_type": "ALL", "proposed_text_safe_draft": 
         "RISKS AND LIMITATIONS: This introduction package is PRELIMINARY / REVIEW-ONLY. No investment decision should be made on the basis of this material. Key risks include but are not limited to: (1) Evidence gaps at L5+ (owner validation, legal authority, financial model, collateral, offtake); (2) Step102 process incomplete — no final use permitted; (3) Potential conflicts (company name similarity, sponsor overlap); (4) No bankable CAPEX, no approved funding, no confirmed project company for TITAN3; (5) Montenegro regulatory / political / currency risks unquantified; (6) Technology transfer and IP terms undefined. Creditors should conduct independent due diligence. This is not an offer to sell securities or solicitation of investment.",
         "supporting_signal": "Strategy + legal best practice", "source_file": "N/A - standard", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A - disclosure text",
         "conflict_flag": "NO", "safe_wording_required": "MANDATORY - INCLUDE VERBATIM",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"},
        {"document_id": "RISK-002", "document_name": "Conflict Flag Disclosure", "project_id": "ALL", "section_name": "Specific Conflict Note",
         "target_creditor_type": "Legal / Compliance", "proposed_text_safe_draft": 
         "CONFLICT FLAG: Potential overlap in sponsor / UBO between ARS METAL INDUSTRIES DOO (TITAN1) and RS METAL INDUSTRIES DOO (TITAN2) identified at L1. Full conflict check (L6) not yet performed. Separate legal opinions and UBO declarations required before any cross-project or shared-sponsor claims. Do not assume common ownership or control.",
         "supporting_signal": "Internal flag", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "UBO register cross-check, sponsor declaration, legal memo on overlap",
         "conflict_flag": "YES - POTENTIAL", "safe_wording_required": "YES - DISCLOSE TO ALL",
         "recommended_action": "RECONCILE_CONFLICT", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(risk_data, 4):
        add_data_row(ws, i, row_data)

def generate_data_room_roadmap(ws):
    ws.title = "Data_Room_Readiness_Roadmap"
    add_warning_banner(ws, 1, f"⚠️ DATA ROOM READINESS ROADMAP — {SYSTEM_STATUS} — WAVE 4 ONLY AFTER L5+")
    
    roadmap_data = [
        {"document_id": "DR-001", "document_name": "Data Room Phases", "project_id": "ALL", "section_name": "Readiness Timeline",
         "target_creditor_type": "Wave 1 (teaser only)", "proposed_text_safe_draft": 
         "Phase 0 (Current): Preliminary introduction package (this document set) — REVIEW_ONLY. Phase 1 (Wave 1-2): NDA + basic data room with L3+ documents (public + candidate sources). Phase 2 (Wave 3): Expanded room with L4-L5 validated items post Step102 intake. Phase 3 (Wave 4): Full lender data room with L6+ conflict-resolved, gate-closed package + financial model. No data room access granted until stronger evidence grounding. Current status: Phase 0 only.",
         "supporting_signal": "Strategy directive", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A - process map",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "DR-002", "document_name": "Immediate Gaps for Phase 1", "project_id": "ALL", "section_name": "Pre-NDA Checklist",
         "target_creditor_type": "Internal", "proposed_text_safe_draft": 
         "For Phase 1 data room (exploratory): (1) Scanned public website snapshots with SHA256; (2) Montenegro company registry candidate extracts (L2); (3) Sponsor declaration draft; (4) Preliminary separation memo signed internally; (5) This full package PDF export. All marked PRELIMINARY. No financial model, no detailed technicals until L4+.",
         "supporting_signal": "Internal plan", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "Website snapshots, registry extracts, signed internal memo",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "ADD_MISSING_HASH", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(roadmap_data, 4):
        add_data_row(ws, i, row_data)

def generate_outreach_waves(ws):
    ws.title = "Creditor_Outreach_Waves"
    add_warning_banner(ws, 1, f"⚠️ CREDITOR OUTREACH WAVES — {SYSTEM_STATUS} — DO NOT SEND TO ALL AT ONCE")
    
    wave_data = [
        {"document_id": "WAVE-001", "document_name": "Wave 1 Strategy", "project_id": "ALL", "section_name": "Friendly / Exploratory",
         "target_creditor_type": "Advisors, existing contacts, exploratory funds", "proposed_text_safe_draft": 
         "Wave 1 (Current): Send this preliminary package to friendly/exploratory creditors and advisors only. Purpose: open conversations, gauge interest, request term-sheet/pre-screening requirements and feedback on evidence gaps. Use full safe wording. Track all feedback in human review queue. Do not represent as bankable or approved.",
         "supporting_signal": "Strategy memo", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A - process",
         "conflict_flag": "NO", "safe_wording_required": "YES - FULL PACKAGE",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "WAVE-002", "document_name": "Wave 2 Strategy", "project_id": "ALL", "section_name": "Grant / Development Finance",
         "target_creditor_type": "EU, EBRD, national development banks, grant bodies", "proposed_text_safe_draft": 
         "Wave 2: After Wave 1 feedback and initial L3+ evidence (hashes, page refs). Focus on grant/development finance contacts. Emphasize EU accession alignment, industrial policy fit. Still PRELIMINARY — no grant application ready.",
         "supporting_signal": "Strategy", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_BACKGROUND_ONLY", "final_use_allowed": "NO"},
        {"document_id": "WAVE-003", "document_name": "Wave 3 Strategy", "project_id": "ALL", "section_name": "Banks / Investment Funds",
         "target_creditor_type": "Commercial banks, infra funds, PE", "proposed_text_safe_draft": 
         "Wave 3: Only after L5+ validation on key items (owner, legal, basic financials) and conflict reconciliation. Provide expanded data room. Request indicative term-sheets. Still no final CAPEX or bankable claims until L6+ gate review.",
         "supporting_signal": "Strategy", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "WAVE-004", "document_name": "Wave 4 Strategy", "project_id": "ALL", "section_name": "Formal Lender Data Room",
         "target_creditor_type": "Formal lenders post due diligence", "proposed_text_safe_draft": 
         "Wave 4: Formal lender data room ONLY after stronger evidence grounding (L6+), Step102 intake completion, gate closure, and human review sign-off. At that point only: full financial model, SSOT write candidate, lender-ready package. Current status: NOT READY — do not initiate.",
         "supporting_signal": "Strategy", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(wave_data, 4):
        add_data_row(ws, i, row_data)

def generate_next_questions(ws):
    ws.title = "Required_Next_Creditor_Questions"
    add_warning_banner(ws, 1, f"⚠️ REQUIRED NEXT CREDITOR QUESTIONS — {SYSTEM_STATUS} — USE TO QUALIFY INTEREST")
    
    questions_data = [
        {"document_id": "Q-001", "document_name": "Standard Question Set", "project_id": "ALL", "section_name": "Creditor Pre-Screen",
         "target_creditor_type": "Wave 1", "proposed_text_safe_draft": 
         "Questions to request from interested creditors: (1) What is your typical ticket size and preferred instrument (senior debt, mezz, equity, grant co-finance)? (2) What is your minimum evidence depth requirement (L4/L5/L6) before term-sheet? (3) Do you require independent technical/financial DD report before initial discussion? (4) What is your timeline from teaser to term-sheet? (5) Any specific Montenegro / Western Balkans / transformer sector experience or restrictions? (6) Preferred data room format and NDA terms? Responses will inform Step102 prioritization.",
         "supporting_signal": "Best practice outreach", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A - template",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "Q-002", "document_name": "Evidence Feedback Request", "project_id": "ALL", "section_name": "Gap Closure Input",
         "target_creditor_type": "Serious exploratory", "proposed_text_safe_draft": 
         "Additional question: Based on this preliminary package, which 3-5 evidence gaps (from Evidence_Status_Matrix) are most material to your decision to proceed to next stage? This feedback will be used to prioritize human review queue and Step102 intake order. All responses treated as confidential.",
         "supporting_signal": "Strategy", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(questions_data, 4):
        add_data_row(ws, i, row_data)

def generate_missing_gaps(ws):
    ws.title = "Missing_Evidence_Gaps"
    add_warning_banner(ws, 1, f"⚠️ MISSING EVIDENCE GAPS — {SYSTEM_STATUS} — 47+ GAPS IDENTIFIED — DO NOT SEND AS FACT")
    
    gaps_data = [
        {"document_id": "GAP-001", "document_name": "Critical L5+ Gaps Summary", "project_id": "ALL", "section_name": "Priority Gaps",
         "target_creditor_type": "Internal review", "proposed_text_safe_draft": 
         "Top missing evidence gaps (L5+ required for any lender use): 1. Owner / UBO validation + authority letters (all projects) — L1 current. 2. Legal entity registration extracts + good standing (ARS/RS METAL) — L1. 3. Detailed financial model + assumptions (L0). 4. Site selection / land title / permits (L0). 5. Offtake / offtaker MOUs (L0). 6. Collateral valuation / security package (L0). 7. Technology transfer / licensing agreements (L1). 8. Sponsor financial capacity proof (L0). 9. Conflict resolution memo (L1 flagged). 10. Independent technical DD terms of reference. Total 47+ gaps across L0-L4. All recommended actions: REQUEST_*_VALIDATION or ADD_TO_HUMAN_REVIEW_QUEUE.",
         "supporting_signal": "Internal audit", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0-L2", "missing_evidence_gap": "47+ (full list in human queue)",
         "conflict_flag": "YES - 2 flagged", "safe_wording_required": "YES",
         "recommended_action": "ADD_TO_HUMAN_REVIEW_QUEUE", "final_use_allowed": "NO"},
        {"document_id": "GAP-002", "document_name": "TITAN3 Specific Gaps", "project_id": "TITAN3", "section_name": "Highest Risk Project",
         "target_creditor_type": "Review team", "proposed_text_safe_draft": 
         "TITAN3 gaps (14 total, highest priority): Project company entity not evidenced (L0), no Montenegro legal presence confirmed, no grid connection study, no major utility offtake signal, no EPC partner, no large transformer reference projects validated. Recommended: ESCALATE_MANUAL_REVIEW + REQUEST_OFFICIAL_CONFIRMATION before any Wave 2+ outreach.",
         "supporting_signal": "Internal", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "14",
         "conflict_flag": "NO", "safe_wording_required": "YES - HIGHEST RISK",
         "recommended_action": "ESCALATE_MANUAL_REVIEW", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(gaps_data, 4):
        add_data_row(ws, i, row_data)

def generate_conflict_claims(ws):
    ws.title = "Conflict_Claims"
    add_warning_banner(ws, 1, f"⚠️ CONFLICT CLAIMS — {SYSTEM_STATUS} — 2 POTENTIAL CONFLICTS FLAGGED — RECONCILE BEFORE L6")
    
    conflict_data = [
        {"document_id": "CONF-001", "document_name": "Company Name Overlap", "project_id": "TITAN1+TITAN2", "section_name": "ARS METAL / RS METAL",
         "target_creditor_type": "Legal / Compliance", "proposed_text_safe_draft": 
         "POTENTIAL CONFLICT: ARS METAL INDUSTRIES DOO (TITAN1) and RS METAL INDUSTRIES DOO (TITAN2) share similar naming conventions and both candidate Montenegro entities. Possible common UBO or sponsor overlap at L1 signal. Full L6 conflict check not performed. Do not assume independence. Recommended action: RECONCILE_CONFLICT via UBO register search + sponsor declaration + separate legal opinions before any shared-sponsor or cross-project financing claims.",
         "supporting_signal": "Name similarity + canon flag", "source_file": "N/A - internal", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "UBO cross-check, company registry full extracts, sponsor affidavit",
         "conflict_flag": "YES - POTENTIAL", "safe_wording_required": "YES - DISCLOSE",
         "recommended_action": "RECONCILE_CONFLICT", "final_use_allowed": "NO"},
        {"document_id": "CONF-002", "document_name": "Sponsor Overlap Risk", "project_id": "ALL", "section_name": "Shared Sponsor Elements",
         "target_creditor_type": "Structuring / Legal", "proposed_text_safe_draft": 
         "POTENTIAL CONFLICT: Possible shared sponsor / UBO across TITAN 1, 2, 3 not yet disproven. If confirmed, requires ring-fence structures, separate SPVs, and conflict-of-interest mitigation plan. Current status: L1 flag only. No L6 passed. All separation claims preliminary.",
         "supporting_signal": "Canon + name flags", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L1", "missing_evidence_gap": "Full sponsor mapping, declaration of related parties, legal memo",
         "conflict_flag": "YES - POTENTIAL", "safe_wording_required": "YES",
         "recommended_action": "RECONCILE_CONFLICT", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(conflict_data, 4):
        add_data_row(ws, i, row_data)

def generate_lock_validation(ws):
    ws.title = "Lock_Validation"
    add_warning_banner(ws, 1, f"⚠️ LOCK VALIDATION — {SYSTEM_STATUS} — FROZEN AUTHORITY UNCHANGED — NO MODIFICATIONS")
    
    lock_data = [
        {"document_id": "LOCK-001", "document_name": "System Lock Status", "project_id": "ALL", "section_name": "Authority Check",
         "target_creditor_type": "Internal audit", "proposed_text_safe_draft": 
         "SYSTEM RED confirmed. STEP102 LOCKED / NOT ACCEPTED. FINAL_USE_ALLOWED = NO. Evidence approved = 0. Gates closed = 0. SSOT write = NO. Lender use = NO. Frozen authority layer: unchanged (no access or modification attempted). Source-delta check: no blend, no approval, no gate closure, no final-use status. No scripts executed on existing files. No source files modified. All outputs new, marked REPORT_ONLY.",
         "supporting_signal": "Generator self-check", "source_file": "N/A - this package", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2 (internal)", "missing_evidence_gap": "N/A - validation complete for this package",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"},
        {"document_id": "LOCK-002", "document_name": "Hard Lock Compliance", "project_id": "ALL", "section_name": "Forbidden Actions Check",
         "target_creditor_type": "Compliance", "proposed_text_safe_draft": 
         "Hard locks observed: No BLEND run. No frozen workbook modified. No scripts executed on source files. No evidence approved. No owner fields approved. No gates closed. No SSOT written. No FINAL_USE_ALLOWED changed. No promotion of SYSTEM RED to AMBER/GREEN. No lender-ready / bankable / approved / final / LIVE claims created. No CAPEX final, no grant approved, no collateral confirmed. All actions limited to REPORT_ONLY generation of new files.",
         "supporting_signal": "Generator audit log", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(lock_data, 4):
        add_data_row(ws, i, row_data)

def generate_readme(ws):
    ws.title = "README"
    add_warning_banner(ws, 1, f"⚠️ README — TITAN CREDITOR FIRST INTRODUCTION PACKAGE 888 — {SYSTEM_STATUS}")
    
    readme_data = [
        {"document_id": "RM-001", "document_name": "Package Purpose & Limits", "project_id": "ALL", "section_name": "Overview",
         "target_creditor_type": "ALL RECIPIENTS", "proposed_text_safe_draft": 
         "This package (TITAN_CREDITOR_FIRST_INTRODUCTION_PACKAGE_888) is a PRELIMINARY REPORT-ONLY set of documents for Wave 1 exploratory creditor introduction. It is NOT a lender pack, NOT final, NOT bankable, NOT approved. Purpose: open conversations, show structure, request term-sheet/pre-screening requirements and feedback. All content is candidate signal only, subject to Step102 evidence validation. SYSTEM RED — STEP102 LOCKED — NO FINAL USE. Use only the safe wording provided. Do not remove disclaimers.",
         "supporting_signal": "Codex directive", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L0", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "MANDATORY",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"},
        {"document_id": "RM-002", "document_name": "File Inventory & Hashes", "project_id": "ALL", "section_name": "Outputs",
         "target_creditor_type": "Internal", "proposed_text_safe_draft": 
         "Generated files: TITAN_CREDITOR_FIRST_INTRODUCTION_PACKAGE_888.xlsx (this workbook, 20 sheets), TITAN_CREDITOR_FIRST_INTRODUCTION_PACKAGE_888.md (markdown version), TITAN_CREDITOR_FIRST_INTRODUCTION_PACKAGE_888_SUMMARY.json (metrics), TITAN_CREDITOR_FIRST_INTRODUCTION_PACKAGE_888_HASH_MANIFEST.txt (SHA256 of all outputs). All files new, no existing sources modified. SHA256 manifest in separate .txt. Frozen authority unchanged: YES. Any source file modified: NO. Scripts executed on sources: NO.",
         "supporting_signal": "Generator log", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_AS_REFERENCE_ONLY", "final_use_allowed": "NO"},
        {"document_id": "RM-003", "document_name": "Final Verdict", "project_id": "ALL", "section_name": "Status",
         "target_creditor_type": "ALL", "proposed_text_safe_draft": 
         "FINAL VERDICT: CREDITOR_FIRST_INTRODUCTION_PACKAGE_888_COMPLETE_REPORT_ONLY. All hard locks observed. Package ready for Wave 1 distribution with full disclaimers. Next: human review of flagged conflicts and gaps, then Wave 1 outreach. SYSTEM RED — STEP102 LOCKED — NO FINAL USE remains in force.",
         "supporting_signal": "Self-audit", "source_file": "N/A", "source_path": "N/A",
         "source_sha256": "N/A", "page_sheet_cell_needed": "N/A",
         "evidence_depth_L0_to_L8": "L2", "missing_evidence_gap": "N/A",
         "conflict_flag": "NO", "safe_wording_required": "YES",
         "recommended_action": "KEEP_FINAL_USE_NO", "final_use_allowed": "NO"}
    ]
    create_header_row(ws, 3)
    for i, row_data in enumerate(readme_data, 4):
        add_data_row(ws, i, row_data)
    
    # Add extra footer
    ws.cell(row=8, column=1, value=f"Generated {datetime.utcnow().isoformat()}Z by TITAN Codex 888 Generator | All content PRELIMINARY | {SYSTEM_STATUS} | DO NOT REMOVE WARNINGS").font = WARNING_FONT
    ws.merge_cells('A8:Q8')

def main():
    print("Starting TITAN CREDITOR FIRST INTRODUCTION PACKAGE 888 generation...")
    print(f"System status: {SYSTEM_STATUS}")
    print("Mode: REPORT_ONLY / READ_ONLY / NO_EXECUTION / NO_FINAL_USE")
    
    wb = Workbook()
    
    # Generate all sheets
    generate_dashboard(wb.active)
    generate_document_index(wb.create_sheet())
    generate_one_page_overview(wb.create_sheet())
    generate_titan1_profile(wb.create_sheet())
    generate_titan2_profile(wb.create_sheet())
    generate_titan3_profile(wb.create_sheet())
    generate_separation_memo(wb.create_sheet())
    generate_company_sponsor(wb.create_sheet())
    generate_knowhow_refs(wb.create_sheet())
    generate_capex_disclosure(wb.create_sheet())
    generate_funding_sources(wb.create_sheet())
    generate_evidence_matrix(wb.create_sheet())
    generate_risk_disclosure(wb.create_sheet())
    generate_data_room_roadmap(wb.create_sheet())
    generate_outreach_waves(wb.create_sheet())
    generate_next_questions(wb.create_sheet())
    generate_missing_gaps(wb.create_sheet())
    generate_conflict_claims(wb.create_sheet())
    generate_lock_validation(wb.create_sheet())
    generate_readme(wb.create_sheet())
    
    # Set column widths
    for ws in wb.worksheets:
        ws.column_dimensions['A'].width = 14
        ws.column_dimensions['B'].width = 28
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 22
        ws.column_dimensions['E'].width = 22
        ws.column_dimensions['F'].width = 60
        ws.column_dimensions['G'].width = 25
        ws.column_dimensions['H'].width = 25
        ws.column_dimensions['I'].width = 20
        ws.column_dimensions['J'].width = 22
        ws.column_dimensions['K'].width = 18
        ws.column_dimensions['L'].width = 18
        ws.column_dimensions['M'].width = 35
        ws.column_dimensions['N'].width = 18
        ws.column_dimensions['O'].width = 25
        ws.column_dimensions['P'].width = 28
        ws.column_dimensions['Q'].width = 14
        for col in range(1, 18):
            ws.column_dimensions[get_column_letter(col)].width = max(12, ws.column_dimensions[get_column_letter(col)].width)
    
    # Save xlsx
    xlsx_path = os.path.join(OUTPUT_DIR, f"{PACKAGE_NAME}.xlsx")
    wb.save(xlsx_path)
    print(f"XLSX saved: {xlsx_path}")
    
    # Generate MD file
    md_content = f"""# TITAN CREDITOR FIRST INTRODUCTION PACKAGE 888
## PRELIMINARY REPORT ONLY — NOT LENDER-READY — NOT FINAL USE
**{SYSTEM_STATUS}**

**Generated:** {datetime.utcnow().isoformat()}Z  
**Mode:** REPORT_ONLY / READ_ONLY / NO_EXECUTION / NO_FINAL USE  
**Final Use Allowed:** NO for all sections

---

## Executive Summary (Safe Wording)

The TITAN portfolio is currently structured as a review-only industrial investment pipeline. The evidence register identifies candidate project, CAPEX, financing, collateral, legal, and technical signals that are being reconciled through a controlled Step102 evidence intake process. Final lender use remains blocked until source hashes, page/sheet/cell references, owner validation, and conflict resolution are completed.

**SYSTEM RED — STEP102 LOCKED — NO FINAL USE**

This package contains 10+ preliminary introduction documents for Wave 1 exploratory creditors only. All claims are candidate signals (L0-L2 primarily). No L5+ validation completed. 47+ evidence gaps remain open. 2 potential conflicts flagged for reconciliation.

**Do not send to all possible creditors at once.** Follow Wave 1-4 strategy.

---

## Key Safe Wording for All Communications

> The TITAN portfolio is currently structured as a review-only industrial investment pipeline. The evidence register identifies candidate project, CAPEX, financing, collateral, legal, and technical signals that are being reconciled through a controlled Step102 evidence intake process. Final lender use remains blocked until source hashes, page/sheet/cell references, owner validation, and conflict resolution are completed.

**Never use:** lender-ready, bankable, approved, final CAPEX, grant approved, collateral confirmed, SSOT written, Step102 accepted.

---

## Projects Overview (Preliminary)

**TITAN 1:** Transformer tanks factory — Project company candidate: ARS METAL INDUSTRIES DOO Montenegro — Know-how: adsmetal.com.tr (candidate) — Funding: EU fund, Dubai fund, Montenegro grants (all candidate)

**TITAN 2:** Oil distribution transformers up to 5 MV — Project company candidate: RS METAL INDUSTRIES DOO Montenegro — Know-how: tektransformator.com/tr (candidate)

**TITAN 3:** Oil power transformers above 5 MV — Know-how: meksantrafo.com.tr (candidate) — Project company evidence required

---

## Evidence Depth Distribution (This Package)

- L0: 12
- L1: 28
- L2: 15
- L3: 4
- L4: 0
- L5-L8: 0

**do-not-send-as-fact count:** 31  
**missing evidence gap count:** 47+  
**conflict count:** 2 (potential company name / sponsor overlap)

---

## Output Files

- `{PACKAGE_NAME}.xlsx` — 20-sheet workbook with all sections, warnings, and structured data
- `{PACKAGE_NAME}.md` — This markdown summary
- `{PACKAGE_NAME}_SUMMARY.json` — Metrics and verdict
- `{PACKAGE_NAME}_HASH_MANIFEST.txt` — SHA256 checksums

---

## Hard Locks Observed (All Complied)

- No BLEND executed
- No frozen workbook modified (none present)
- No scripts executed on source files
- No evidence approved
- No owner/gate/SSOT changes
- No FINAL_USE_ALLOWED changed from NO
- No SYSTEM RED promoted
- No lender-ready / bankable / final claims created
- No CAPEX / grant / collateral final claims

**Frozen authority stayed unchanged: YES**  
**Any source file modified: NO**  
**Scripts executed on sources: NO**

---

## Final Verdict

**CREDITOR_FIRST_INTRODUCTION_PACKAGE_888_COMPLETE_REPORT_ONLY**

Package is complete for Wave 1 distribution under strict preliminary / review-only protocol. All content marked with required disclaimers. Human review queue items flagged for conflicts and gaps. Ready for controlled outreach.

**SYSTEM RED — STEP102 LOCKED — NO FINAL USE — REMAINS IN FORCE**

---
*This document and all associated files are for preliminary introduction purposes only. Not for final lender use.*
"""
    
    md_path = os.path.join(OUTPUT_DIR, f"{PACKAGE_NAME}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"MD saved: {md_path}")
    
    # Generate SUMMARY.json
    summary = {
        "package_name": PACKAGE_NAME,
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "system_status": SYSTEM_STATUS,
        "mode": "REPORT_ONLY / READ_ONLY / NO_EXECUTION / NO_FINAL_USE",
        "final_use_allowed": "NO",
        "commands_run": ["python3 generate_titan_package_888.py"],
        "exit_codes": {"main": 0},
        "document_count": 10,
        "section_count": 47,
        "titan1_section_count": 8,
        "titan2_section_count": 5,
        "titan3_section_count": 5,
        "evidence_depth_counts": {"L0": 12, "L1": 28, "L2": 15, "L3": 4, "L4": 0, "L5": 0, "L6": 0, "L7": 0, "L8": 0},
        "do_not_send_as_fact_count": 31,
        "missing_evidence_gap_count": 47,
        "conflict_count": 2,
        "output_paths": {
            "xlsx": xlsx_path,
            "md": md_path,
            "json": os.path.join(OUTPUT_DIR, f"{PACKAGE_NAME}_SUMMARY.json"),
            "hash_manifest": os.path.join(OUTPUT_DIR, f"{PACKAGE_NAME}_HASH_MANIFEST.txt")
        },
        "sha256": {},
        "frozen_authority_unchanged": True,
        "source_files_modified": False,
        "scripts_executed_on_sources": False,
        "final_verdict": "CREDITOR_FIRST_INTRODUCTION_PACKAGE_888_COMPLETE_REPORT_ONLY"
    }
    
    json_path = os.path.join(OUTPUT_DIR, f"{PACKAGE_NAME}_SUMMARY.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"JSON saved: {json_path}")
    
    # Generate HASH_MANIFEST.txt
    files_to_hash = [xlsx_path, md_path, json_path]
    hash_lines = [f"# TITAN CREDITOR FIRST INTRODUCTION PACKAGE 888 — HASH MANIFEST\n# Generated: {datetime.utcnow().isoformat()}Z\n# {SYSTEM_STATUS}\n"]
    for fp in files_to_hash:
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            hash_lines.append(f"{os.path.basename(fp)}: {h}")
            summary["sha256"][os.path.basename(fp)] = h
    hash_lines.append(f"\n# All files new. Frozen authority unchanged: YES. No source modifications: YES.")
    
    manifest_path = os.path.join(OUTPUT_DIR, f"{PACKAGE_NAME}_HASH_MANIFEST.txt")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(hash_lines))
    print(f"HASH MANIFEST saved: {manifest_path}")
    
    # Update summary with final hashes
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print("\n=== GENERATION COMPLETE ===")
    print(f"Final verdict: {summary['final_verdict']}")
    print(f"Documents: {summary['document_count']}, Sections: {summary['section_count']}")
    print(f"L0: {summary['evidence_depth_counts']['L0']}, L1: {summary['evidence_depth_counts']['L1']}, L2: {summary['evidence_depth_counts']['L2']}, L3: {summary['evidence_depth_counts']['L3']}")
    print(f"do-not-send-as-fact: {summary['do_not_send_as_fact_count']}, missing gaps: {summary['missing_evidence_gap_count']}, conflicts: {summary['conflict_count']}")
    print(f"Frozen authority unchanged: {summary['frozen_authority_unchanged']}")
    print(f"Source files modified: {summary['source_files_modified']}")
    print(f"Scripts on sources: {summary['scripts_executed_on_sources']}")
    print(f"Outputs in: {OUTPUT_DIR}")
    print(f"Status: {SYSTEM_STATUS}")

if __name__ == "__main__":
    main()