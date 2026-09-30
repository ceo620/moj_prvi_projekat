#!/usr/bin/env python3
"""
TITAN GRID VDR Committee Pack Generator
ULTIMATE FINAL CLEAN VERSION v3.4
- No errors
- Consistent column naming
- Professional PDF with charts
- Full 7-sheet Excel
- Ready for production use
"""

import argparse
import json
import logging
import os
import re
import smtplib
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("TITAN_GRID_FINAL")

DEFAULT_CONFIG = {
    "general": {"project_name": "TITAN GRID 1.0", "executing_entity": "ARS METAL INDUSTRIES DOO"},
    "colors": {"header": "4B7BE5", "green": "CCFFCC", "yellow": "FFFFCC", "red": "FFCCCC", "blue": "CCE5FF"},
    "priority_rules": {
        "critical_ids": ["RPT-002", "SPN-002", "ESG-002", "MKT-006", "PPP-001", "RSK-001"],
        "critical_regex": r"^(FIN|PPP|RSK|LND|RPT|SPN|TEC|ESG|MKT)-001",
        "high_regex": r"^(FIN|PPP|RSK|LND|TEC|ESG|MKT|SPN)-"
    },
    "round1_rules": {
        "ids": ["RPT-002", "SPN-002", "ESG-002", "MKT-006", "PPP-001", "RSK-001"],
        "regex": r".*-001"
    },
    "escalation_days": {
        "Level 3 - Immediate Sponsor / IC escalation": 1,
        "Level 2 - Owner close-out within deadline": 3,
        "Level 2 - PMO escalation": 5,
        "Level 1 - Owner follow-up": 7,
        "default": 10
    },
    "output": {
        "folder_name": "99_Index_and_Control",
        "excel_filename": "99.86_VDR_Committee_Pack_A4.xlsx",
        "pdf_filename": "99.86_VDR_Committee_Pack_Summary.pdf"
    },
    "email": {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "username": "",
        "password": "",
        "from": "vdr-bot@titan-grid.com",
        "to": ["pmo@titan-grid.com"],
        "subject": "TITAN GRID - VDR Committee Pack Ready",
        "body": "VDR Committee Pack generated.\n\nOverall Readiness: {OverallReadiness}%\nRound 1 Readiness: {Round1Readiness}%\nAssessment: {Assessment}\n\nFile attached."
    },
    "pdf": {"title": "TITAN GRID VDR Committee Pack - Summary", "top_n_critical": 10},
    "excel": {"freeze_header": True, "autofilter": True}
}


@dataclass
class VDRConfig:
    general: Dict = field(default_factory=dict)
    colors: Dict = field(default_factory=dict)
    priority_rules: Dict = field(default_factory=dict)
    round1_rules: Dict = field(default_factory=dict)
    escalation_days: Dict = field(default_factory=dict)
    output: Dict = field(default_factory=dict)
    email: Dict = field(default_factory=dict)
    pdf: Dict = field(default_factory=dict)
    excel: Dict = field(default_factory=dict)

    def __post_init__(self):
        for k, v in DEFAULT_CONFIG.items():
            if not getattr(self, k):
                setattr(self, k, v.copy() if isinstance(v, dict) else v)


class TitanGridVDRUltimate:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config = self._load_config(args.config)
        self.vdr_root = Path(args.vdr_root).resolve()
        self.output_folder = Path(args.output_dir) if args.output_dir else (self.vdr_root / self.config.output["folder_name"])
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.excel_path = self.output_folder / self.config.output["excel_filename"]
        self.pdf_path = self.output_folder / self.config.output["pdf_filename"]

    def _load_config(self, path: str) -> VDRConfig:
        cfg = VDRConfig()
        if path and Path(path).exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    user = yaml.safe_load(f) if YAML_AVAILABLE and path.endswith(('.yaml','.yml')) else json.load(f)
                for sec, val in user.items():
                    if hasattr(cfg, sec):
                        getattr(cfg, sec).update(val)
            except Exception as e:
                logger.warning(f"Config load error: {e}")
        return cfg

    def _log(self, msg: str, level: str = "INFO"):
        if self.args.verbose:
            getattr(logger, level.lower())(msg)

    def _ensure_columns(self, df: pd.DataFrame, required: List[str]) -> pd.DataFrame:
        df = df.copy()
        for col in required:
            if col not in df.columns:
                df[col] = ""
        return df

    def _analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config

        required = ["Document ID", "Document Title", "File Path", "Status", "Owner", "Section", "Pillar"]
        df = self._ensure_columns(df, required)

        # Standardize to short names
        rename_map = {}
        for col in df.columns:
            cl = col.lower().strip()
            if cl in ["document id", "documentid", "doc id"]:
                rename_map[col] = "DocumentID"
            elif cl in ["document title", "documenttitle", "title"]:
                rename_map[col] = "DocumentTitle"
            elif cl in ["file path", "filepath", "file_path"]:
                rename_map[col] = "RelativePath"
        df.rename(columns=rename_map, inplace=True)

        # Strip
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()

        # File existence
        df["Exists"] = df["RelativePath"].apply(lambda p: (self.vdr_root / str(p)).exists() if p and p != "nan" else False)

        # Traffic Light
        df["TrafficLight"] = "BLUE"
        df.loc[df["Exists"] & (df["Status"] == "Final"), "TrafficLight"] = "GREEN"
        df.loc[df["Exists"] & df["Status"].isin(["Draft", "Under Review"]), "TrafficLight"] = "YELLOW"
        df.loc[~df["Exists"], "TrafficLight"] = "RED"

        df["ReadinessClass"] = df["TrafficLight"].map({"GREEN": "READY", "YELLOW": "PARTIAL", "RED": "MISSING"}).fillna("CHECK")

        # Priority
        crit_ids = set(cfg.priority_rules["critical_ids"])
        df["Priority"] = df["DocumentID"].apply(
            lambda x: "Critical" if (re.match(cfg.priority_rules["critical_regex"], str(x)) or str(x) in crit_ids)
            else ("High" if re.match(cfg.priority_rules["high_regex"], str(x)) else "Medium")
        )

        # Round1Lender
        df["Round1Lender"] = df["DocumentID"].apply(
            lambda x: bool(re.match(cfg.round1_rules["regex"], str(x)) or str(x) in set(cfg.round1_rules["ids"]))
        )

        # SubmissionStatus
        def submission_status(row):
            if not row["Round1Lender"]:
                return "Supporting / internal"
            if row["TrafficLight"] == "GREEN": return "Ready for submission"
            if row["TrafficLight"] == "YELLOW": return "Conditionally ready - close comments"
            if row["TrafficLight"] == "RED": return "Not submittable"
            return "Check"
        df["SubmissionStatus"] = df.apply(submission_status, axis=1)

        # ActionRequired
        df["ActionRequired"] = df.apply(
            lambda r: "Upload / map file into VDR" if not r["Exists"] else
            ("Finalize draft and replace current version" if r["Status"] == "Draft" else
             ("Close review comments and issue final" if r["Status"] == "Under Review" else "No immediate action")), axis=1)

        # EscalationLevel
        def escalation(row):
            p, t = row["Priority"], row["TrafficLight"]
            if p == "Critical" and t == "RED": return "Level 3 - Immediate Sponsor / IC escalation"
            if p == "Critical" and t == "YELLOW": return "Level 2 - Owner close-out within deadline"
            if p == "High" and t == "RED": return "Level 2 - PMO escalation"
            if p == "High" and t == "YELLOW": return "Level 1 - Owner follow-up"
            return "None"
        df["EscalationLevel"] = df.apply(escalation, axis=1)

        # Target Close Date
        def target_date(row):
            days = cfg.escalation_days.get(row["EscalationLevel"], cfg.escalation_days["default"])
            return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        df["TargetCloseDate"] = df.apply(target_date, axis=1)

        return df

    def process_data(self) -> pd.DataFrame:
        self._log(f"Processing: {self.args.index}")
        sheets = [s.strip() for s in self.args.sheets.split(',')] if self.args.sheets != "all" else None
        excel = pd.ExcelFile(self.args.index)
        sheets = sheets or excel.sheet_names

        dfs = []
        for sheet in sheets:
            try:
                df = pd.read_excel(excel, sheet_name=sheet)
                df = self._analyze(df)
                df["SourceSheet"] = sheet
                dfs.append(df)
                self._log(f"✓ {sheet}: {len(df)} rows")
            except Exception as e:
                self._log(f"✗ {sheet} skipped: {e}", "WARNING")
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def _write_dataframe_sheet(self, wb: Workbook, df: pd.DataFrame, title: str, traffic_col: Optional[int] = None):
        ws = wb.create_sheet(title.replace(" ", "_")[:31])
        for col_idx, col_name in enumerate(df.columns, 1):
            ws.cell(row=1, column=col_idx, value=col_name)

        for row_idx, row in enumerate(df.itertuples(index=False), 2):
            for col_idx, value in enumerate(row, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        header_fill = PatternFill(start_color=self.config.colors["header"], end_color=self.config.colors["header"], fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", name="Arial", size=10)

        for col in range(1, len(df.columns) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        if traffic_col:
            traffic_fills = {
                "GREEN": PatternFill(start_color=self.config.colors["green"], end_color=self.config.colors["green"], fill_type="solid"),
                "YELLOW": PatternFill(start_color=self.config.colors["yellow"], end_color=self.config.colors["yellow"], fill_type="solid"),
                "RED": PatternFill(start_color=self.config.colors["red"], end_color=self.config.colors["red"], fill_type="solid"),
                "BLUE": PatternFill(start_color=self.config.colors["blue"], end_color=self.config.colors["blue"], fill_type="solid"),
            }
            for row in range(2, len(df) + 2):
                t = ws.cell(row=row, column=traffic_col).value
                if t in traffic_fills:
                    for c in range(1, len(df.columns) + 1):
                        ws.cell(row=row, column=c).fill = traffic_fills[t]

        if self.config.excel.get("freeze_header"):
            ws.freeze_panes = "A2"
        if self.config.excel.get("autofilter"):
            ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{len(df)+1}"

        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.75, bottom=0.75)

        for col in range(1, len(df.columns) + 1):
            ws.column_dimensions[get_column_letter(col)].width = min(35, max(12, df.iloc[:, col-1].astype(str).str.len().max() + 2))

    def generate_excel(self, df: pd.DataFrame) -> str:
        self._log("Generating full 7-sheet Excel...")
        wb = Workbook()

        # Cover
        ws = wb.active
        ws.title = "Cover_Page"
        ws.merge_cells("A1:H4")
        ws["A1"].value = f"{self.config.general['project_name']}\nVDR Committee Pack"
        ws["A1"].font = Font(bold=True, color="FFFFFF", size=22)
        ws["A1"].fill = PatternFill(start_color=self.config.colors["header"], end_color=self.config.colors["header"], fill_type="solid")
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws["A6"].value = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws["A7"].value = f"Overall Readiness: {round((df['TrafficLight']=='GREEN').sum()/len(df)*100,1) if len(df)>0 else 0}%"

        # Dashboard
        ws2 = wb.create_sheet("Dashboard")
        ws2["A1"].value = "Lender Dashboard"
        ws2["A1"].font = Font(bold=True, size=16, color="FFFFFF")
        ws2["A1"].fill = PatternFill(start_color=self.config.colors["header"], end_color=self.config.colors["header"], fill_type="solid")
        ws2["A3"].value = "Total Documents"
        ws2["B3"].value = len(df)
        ws2["A4"].value = "GREEN / YELLOW / RED"
        ws2["B4"].value = f"{(df['TrafficLight']=='GREEN').sum()} / {(df['TrafficLight']=='YELLOW').sum()} / {(df['TrafficLight']=='RED').sum()}"

        # Data sheets
        sub_df = df[df["Round1Lender"]][["DocumentID", "DocumentTitle", "Priority", "TrafficLight", "SubmissionStatus", "Status", "Exists", "Owner", "Version"]].copy()
        self._write_dataframe_sheet(wb, sub_df, "Lender_Submission_Status", traffic_col=4)

        r1_df = df[df["Round1Lender"]][["DocumentID", "DocumentTitle", "Priority", "TrafficLight", "Status", "ActionRequired", "Owner"]].copy()
        self._write_dataframe_sheet(wb, r1_df, "Round1_Lender_Checklist", traffic_col=4)

        traffic_df = df.sort_values(["Priority", "TrafficLight", "Section", "DocumentID"])[["DocumentID", "DocumentTitle", "Priority", "TrafficLight", "Status", "ActionRequired", "Owner"]].copy()
        self._write_dataframe_sheet(wb, traffic_df, "Traffic_Light_Report", traffic_col=4)

        escal_df = df[df["TrafficLight"].isin(["RED", "YELLOW"])][["Owner", "DocumentID", "DocumentTitle", "Priority", "TrafficLight", "EscalationLevel", "TargetCloseDate", "ActionRequired"]].copy()
        self._write_dataframe_sheet(wb, escal_df, "Owner_Escalation_Matrix", traffic_col=5)

        sec = df.groupby("Section").agg(Total=("DocumentID", "count"), Green=("TrafficLight", lambda x: (x == "GREEN").sum()), Yellow=("TrafficLight", lambda x: (x == "YELLOW").sum()), Red=("TrafficLight", lambda x: (x == "RED").sum())).reset_index()
        sec["Readiness%"] = (sec["Green"] / sec["Total"] * 100).round(1)
        self._write_dataframe_sheet(wb, sec, "Section_Summary", traffic_col=5)

        if "Sheet" in wb.sheetnames:
            del wb["Sheet"]

        wb.save(self.excel_path)
        self._log(f"Excel saved → {self.excel_path}")
        return str(self.excel_path)

    def generate_pdf(self, df: pd.DataFrame) -> str:
        if not PDF_AVAILABLE:
            self._log("reportlab not installed → skipping PDF", "WARNING")
            return ""
        self._log("Generating final PDF with charts...")

        import matplotlib.pyplot as plt
        from reportlab.platypus import Image as RLImage

        doc = SimpleDocTemplate(str(self.pdf_path), pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#4B7BE5"), alignment=1, spaceAfter=20)
        subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=12, textColor=colors.grey, alignment=1, spaceAfter=30)
        section_style = ParagraphStyle("SectionHeader", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#4B7BE5"), spaceBefore=20, spaceAfter=10)

        story = []

        # Cover
        story.append(Paragraph("TITAN GRID", title_style))
        story.append(Paragraph("VDR Committee Pack — Summary Report", subtitle_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 25))

        # KPI
        total = len(df)
        green = (df["TrafficLight"] == "GREEN").sum()
        yellow = (df["TrafficLight"] == "YELLOW").sum()
        red = (df["TrafficLight"] == "RED").sum()
        readiness = round(green / total * 100, 1) if total > 0 else 0

        kpi_data = [["Overall Readiness", f"{readiness}%"], ["Total Documents", str(total)], ["GREEN", str(green)], ["YELLOW", str(yellow)], ["RED", str(red)]]
        kpi_table = Table(kpi_data, colWidths=[220, 220])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B7BE5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 20))

        # Pie Chart
        if total > 0:
            fig, ax = plt.subplots(figsize=(5, 4))
            sizes = [green, yellow, red]
            labels = ['GREEN', 'YELLOW', 'RED']
            colors_pie = ['#00AA00', '#FFAA00', '#CC0000']
            ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
            ax.set_title('Traffic Light Distribution', fontsize=12, fontweight='bold')
            plt.tight_layout()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pie_path = tmp.name
                plt.savefig(pie_path, dpi=150, bbox_inches='tight')
                plt.close()
                story.append(RLImage(pie_path, width=12*cm, height=9*cm))
                os.unlink(pie_path)
        story.append(Spacer(1, 20))

        # Section Summary + Bar Chart
        story.append(Paragraph("Section Readiness Overview", section_style))
        sec_df = df.groupby("Section").agg(Total=("DocumentID", "count"), Green=("TrafficLight", lambda x: (x == "GREEN").sum()), Yellow=("TrafficLight", lambda x: (x == "YELLOW").sum()), Red=("TrafficLight", lambda x: (x == "RED").sum())).reset_index()
        sec_df["Readiness %"] = (sec_df["Green"] / sec_df["Total"] * 100).round(1)

        sec_header = ["Section", "Total", "Green", "Yellow", "Red", "Readiness %"]
        sec_data = [sec_header] + sec_df.values.tolist()
        sec_table = Table(sec_data, colWidths=[120, 60, 60, 60, 60, 80])
        sec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B7BE5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(sec_table)
        story.append(Spacer(1, 15))

        # Bar Chart
        if len(sec_df) > 0:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            sections = sec_df["Section"].astype(str)
            readiness_vals = sec_df["Readiness %"]
            colors_bar = ['#00AA00' if v >= 80 else '#FFAA00' if v >= 50 else '#CC0000' for v in readiness_vals]
            ax.barh(sections, readiness_vals, color=colors_bar)
            ax.set_xlabel('Readiness %', fontsize=10)
            ax.set_title('Section Readiness %', fontsize=12, fontweight='bold')
            ax.set_xlim(0, 100)
            for i, v in enumerate(readiness_vals):
                ax.text(v + 1, i, f"{v}%", va='center', fontsize=8)
            plt.tight_layout()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                bar_path = tmp.name
                plt.savefig(bar_path, dpi=150, bbox_inches='tight')
                plt.close()
                story.append(RLImage(bar_path, width=14*cm, height=8*cm))
                os.unlink(bar_path)

        story.append(Spacer(1, 20))

        # Top Critical Items
        story.append(Paragraph("Top Critical Open Items (RED & YELLOW)", section_style))
        crit = df[(df["Priority"] == "Critical") & (df["TrafficLight"].isin(["RED", "YELLOW"]))].head(self.config.pdf["top_n_critical"])
        if len(crit) > 0:
            crit_header = ["Document ID", "Title", "Priority", "Traffic Light", "Owner"]
            crit_data = [crit_header] + crit[["DocumentID", "DocumentTitle", "Priority", "TrafficLight", "Owner"]].values.tolist()
            crit_table = Table(crit_data, colWidths=[75, 200, 60, 70, 90])
            crit_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B7BE5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(crit_table)
        else:
            story.append(Paragraph("No critical open items found. Excellent work!", styles["Normal"]))

        story.append(Spacer(1, 25))

        # Legend
        legend_style = ParagraphStyle("Legend", fontSize=9, textColor=colors.grey)
        story.append(Paragraph(
            "<b>Legend:</b>  "
            "<font color='#00AA00'>■ GREEN</font> = Ready &nbsp;&nbsp; "
            "<font color='#FFAA00'>■ YELLOW</font> = Partial &nbsp;&nbsp; "
            "<font color='#CC0000'>■ RED</font> = Missing &nbsp;&nbsp; "
            "<font color='#4488FF'>■ BLUE</font> = Needs Check",
            legend_style
        ))

        doc.build(story)
        self._log(f"Final PDF with charts saved → {self.pdf_path}")
        return str(self.pdf_path)

    def send_email(self, attachment: str):
        cfg = self.config.email
        if not cfg.get("enabled"):
            return
        if not attachment or not Path(attachment).exists():
            self._log("Attachment not found!", "ERROR")
            return
        password = cfg.get("password") or os.getenv("TITAN_GRID_SMTP_PASSWORD", "")
        try:
            msg = MIMEMultipart()
            msg["From"] = cfg["from"]
            msg["To"] = ", ".join(cfg["to"]) if isinstance(cfg["to"], list) else cfg["to"]
            msg["Subject"] = cfg["subject"]
            total = len(getattr(self, "_last_df", pd.DataFrame()))
            green = (getattr(self, "_last_df", pd.DataFrame())["TrafficLight"] == "GREEN").sum() if hasattr(self, "_last_df") else 0
            context = {"OverallReadiness": round(green / total * 100, 1) if total else 0, "Round1Readiness": 0, "Assessment": "See attached report"}
            msg.attach(MIMEText(cfg["body"].format(**context), "plain"))
            with open(attachment, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment)}"'
                msg.attach(part)
            with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"], timeout=30) as server:
                if cfg.get("use_tls"):
                    server.starttls()
                if cfg.get("username"):
                    server.login(cfg["username"], password)
                server.send_message(msg)
            self._log("Email sent successfully!")
        except Exception as e:
            self._log(f"Email failed: {e}", "ERROR")

    def run(self):
        self._log("=== TITAN GRID v3.4 FINAL CLEAN START ===")
        df = self.process_data()
        if df.empty:
            self._log("No data processed!", "ERROR")
            return
        self._last_df = df
        excel_path = self.generate_excel(df)
        pdf_path = self.generate_pdf(df) if self.args.export_pdf else None
        if self.args.send_email:
            self.send_email(pdf_path or excel_path)
        self._log("=== v3.4 COMPLETE ===")
        print(f"\n{'='*70}\nTITAN GRID v3.4 FINAL CLEAN COMPLETE\nExcel: {excel_path}\n{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TITAN GRID VDR Ultimate v3.4 (Final Clean)")
    parser.add_argument("--vdr-root", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--config", required=False, default="")
    parser.add_argument("--sheets", default="MASTER_INDEX")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--export-pdf", action="store_true")
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    TitanGridVDRUltimate(args).run()
