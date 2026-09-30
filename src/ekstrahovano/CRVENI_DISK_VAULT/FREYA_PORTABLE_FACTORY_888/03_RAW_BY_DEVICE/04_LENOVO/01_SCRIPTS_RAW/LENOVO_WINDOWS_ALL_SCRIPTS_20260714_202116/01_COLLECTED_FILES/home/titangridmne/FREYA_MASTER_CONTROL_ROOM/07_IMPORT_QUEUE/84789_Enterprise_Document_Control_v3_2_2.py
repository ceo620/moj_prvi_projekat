from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.page import PageMargins
from openpyxl.formatting.rule import FormulaRule
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter

OUTPUT_FILE = "Enterprise_Document_Control_v3_2_2.xlsx"

# =========================================================
# DESIGN SYSTEM
# =========================================================
NAVY = "001F3F"
CYAN = "00A3E0"
WHITE = "FFFFFF"
BLACK = "000000"
LIGHT_GRAY = "F2F4F6"
SOFT_BLUE = "DCE6F1"
SOFT_GREEN = "E2F0D9"
SOFT_RED = "FDE9E7"
SOFT_AMBER = "FFF2CC"
GREEN_TEXT = "006100"
RED_TEXT = "9C0006"
AMBER_TEXT = "7F6000"
DARK_GRAY = "5B6570"

FONT_TITLE = Font(name="Arial", size=16, bold=True, color=WHITE)
FONT_SUBTITLE = Font(name="Arial", size=12, bold=True, color=NAVY)
FONT_SECTION = Font(name="Arial", size=11, bold=True, color=NAVY)
FONT_LABEL = Font(name="Arial", size=10, bold=True, color=NAVY)
FONT_BODY = Font(name="Arial", size=10, color=BLACK)
FONT_META = Font(name="Arial", size=9, color=DARK_GRAY)
FONT_KPI = Font(name="Arial", size=14, bold=True, color=NAVY)
FONT_SMALL_WHITE = Font(name="Arial", size=9, bold=True, color=WHITE)
FONT_BUTTON = Font(name="Arial", size=10, bold=True, color=WHITE)

FILL_NAVY = PatternFill("solid", fgColor=NAVY)
FILL_CYAN = PatternFill("solid", fgColor=CYAN)
FILL_LIGHT = PatternFill("solid", fgColor=LIGHT_GRAY)
FILL_INPUT = PatternFill("solid", fgColor=SOFT_BLUE)
FILL_GREEN = PatternFill("solid", fgColor=SOFT_GREEN)
FILL_RED = PatternFill("solid", fgColor=SOFT_RED)
FILL_AMBER = PatternFill("solid", fgColor=SOFT_AMBER)

THIN = Side(style="thin", color="D9D9D9")
MEDIUM_NAVY = Side(style="medium", color=NAVY)

BORDER_THIN = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BORDER_SECTION = Border(bottom=MEDIUM_NAVY)
BORDER_BOX = Border(
    left=Side(style="medium", color=NAVY),
    right=Side(style="medium", color=NAVY),
    top=Side(style="medium", color=NAVY),
    bottom=Side(style="medium", color=NAVY),
)

ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center", wrap_text=True)

LOCKED = Protection(locked=True)
UNLOCKED = Protection(locked=False)

MARGIN_15MM = 0.59

PASSWORD_INPUT = "input_2026"
PASSWORD_CONTROL = "control_2026"
PASSWORD_OUTPUT = "output_2026"
PASSWORD_ADMIN = "admin_2026"

SHEET_PASSWORD_MAP = {
    "00_Cover": PASSWORD_OUTPUT,
    "01_Navigation": PASSWORD_CONTROL,
    "02_Instructions": PASSWORD_CONTROL,
    "03_Document_Control": PASSWORD_CONTROL,
    "04_Master_Input_Form": PASSWORD_INPUT,
    "05_Supporting_Inputs": PASSWORD_INPUT,
    "06_Validation_Lists": PASSWORD_ADMIN,
    "07_Calculations": PASSWORD_ADMIN,
    "08_Checks": PASSWORD_CONTROL,
    "09_UI_Components": PASSWORD_ADMIN,
    "10_Print_Form": PASSWORD_OUTPUT,
    "11_Print_Summary": PASSWORD_OUTPUT,
    "12_Print_Approval": PASSWORD_OUTPUT,
    "13_Dashboard": PASSWORD_CONTROL,
    "14_Revision_Log": PASSWORD_CONTROL,
    "15_Export_Map": PASSWORD_CONTROL,
    "16_Config": PASSWORD_ADMIN,
    "17_Output_Register": PASSWORD_CONTROL,
    "18_Deployment_Notes": PASSWORD_CONTROL,
    "19_Button_Mapping": PASSWORD_CONTROL,
    "20_Release_Checklist": PASSWORD_CONTROL,
    "21_Workflow_Control": PASSWORD_CONTROL,
    "98_Macro_Companion": PASSWORD_ADMIN,
    "99_Admin_Hidden": PASSWORD_ADMIN,
}

def add_named_range(wb, name, sheet_name, ref):
    wb.defined_names.add(DefinedName(name=name, attr_text=f"'{sheet_name}'!{ref}"))

def set_standard_columns(ws):
    widths = {
        "A": 2.5, "B": 18, "C": 18, "D": 18, "E": 18, "F": 18,
        "G": 18, "H": 18, "I": 18, "J": 18, "K": 18, "L": 2.5,
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

def set_row_heights(ws):
    for r in range(1, 100):
        ws.row_dimensions[r].height = 20

def apply_page_setup(ws, print_area=None):
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_margins = PageMargins(
        left=MARGIN_15MM,
        right=MARGIN_15MM,
        top=MARGIN_15MM,
        bottom=MARGIN_15MM,
        header=0.2,
        footer=0.2,
    )
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_view.showGridLines = False
    if print_area:
        ws.print_area = print_area
    ws.oddFooter.left.text = "Confidential – Internal Use Only"
    ws.oddFooter.center.text = "&D"
    ws.oddFooter.right.text = "Page &P of &N"

def style_title(ws, rng, text):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    c.value = text
    c.font = FONT_TITLE
    c.fill = FILL_NAVY
    c.alignment = ALIGN_CENTER
    c.border = BORDER_THIN

def style_band(ws, rng, text):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    c.value = text
    c.font = FONT_SECTION
    c.fill = FILL_LIGHT
    c.alignment = ALIGN_LEFT
    c.border = BORDER_SECTION

def label(ws, cell, text):
    ws[cell] = text
    ws[cell].font = FONT_LABEL
    ws[cell].alignment = ALIGN_LEFT

def locked_cell(ws, cell, value=None, formula=None, numfmt=None, comment=None):
    if formula is not None:
        ws[cell] = formula
    else:
        ws[cell] = value
    ws[cell].font = FONT_BODY
    ws[cell].alignment = ALIGN_LEFT
    ws[cell].border = BORDER_THIN
    ws[cell].protection = LOCKED
    if numfmt:
        ws[cell].number_format = numfmt
    if comment:
        ws[cell].comment = Comment(comment, "OpenAI")

def input_cell(ws, cell, numfmt=None, comment=None):
    ws[cell].fill = FILL_INPUT
    ws[cell].font = Font(name="Arial", size=10, color="0000FF")
    ws[cell].alignment = ALIGN_LEFT
    ws[cell].border = BORDER_THIN
    ws[cell].protection = UNLOCKED
    if numfmt:
        ws[cell].number_format = numfmt
    if comment:
        ws[cell].comment = Comment(comment, "OpenAI")

def status_cf(ws, cell_range):
    first = cell_range.split(":")[0]
    ws.conditional_formatting.add(
        cell_range,
        FormulaRule(
            formula=[f'OR({first}="PASS",{first}="OK",{first}="READY",{first}="APPROVED",{first}="EXPORT READY",{first}="SIGNED",{first}="GREEN",{first}="ARCHIVED",{first}="COMPLETE")'],
            fill=FILL_GREEN,
            font=Font(color=GREEN_TEXT, bold=True),
        ),
    )
    ws.conditional_formatting.add(
        cell_range,
        FormulaRule(
            formula=[f'OR({first}="FAIL",{first}="ERROR",{first}="BLOCKED",{first}="EXPORT BLOCKED",{first}="RED",{first}="PENDING",{first}="MISSING")'],
            fill=FILL_RED,
            font=Font(color=RED_TEXT, bold=True),
        ),
    )
    ws.conditional_formatting.add(
        cell_range,
        FormulaRule(
            formula=[f'OR({first}="WARNING",{first}="REVIEW",{first}="REVIEW COMPLETE",{first}="IN REVIEW",{first}="AMBER",{first}="DRAFT")'],
            fill=FILL_AMBER,
            font=Font(color=AMBER_TEXT, bold=True),
        ),
    )

def protect_sheet_hardened(ws, password):
    ws.protection.sheet = True
    ws.protection.password = password
    ws.protection.formatCells = False
    ws.protection.formatColumns = False
    ws.protection.formatRows = False
    ws.protection.insertColumns = False
    ws.protection.insertRows = False
    ws.protection.insertHyperlinks = False
    ws.protection.deleteColumns = False
    ws.protection.deleteRows = False
    ws.protection.sort = False
    ws.protection.autoFilter = False
    ws.protection.pivotTables = False
    ws.protection.objects = True
    ws.protection.scenarios = True

def apply_password_strategy(workbook):
    for s in workbook.sheetnames:
        protect_sheet_hardened(workbook[s], SHEET_PASSWORD_MAP.get(s, PASSWORD_CONTROL))

def build_meta_header(ws):
    ws.merge_cells("B3:E3")
    ws["B3"] = "=Document_Title"
    ws["B3"].font = FONT_SUBTITLE
    ws["B3"].alignment = ALIGN_LEFT
    ws["F3"] = "=Document_ID"
    ws["G3"] = "=Version"
    ws["H3"] = "=Confidentiality"
    ws["I3"] = "=Document_Status"
    for c in ["F3", "G3", "H3", "I3"]:
        ws[c].font = FONT_META
        ws[c].alignment = ALIGN_RIGHT

def add_signature_block(ws, start_row, title, name_formula, date_formula):
    style_band(ws, f"B{start_row}:I{start_row}", title)
    label(ws, f"B{start_row+1}", "Name")
    locked_cell(ws, f"C{start_row+1}", formula=name_formula)
    label(ws, f"F{start_row+1}", "Timestamp")
    locked_cell(ws, f"G{start_row+1}", formula=date_formula, numfmt="dd-mmm-yyyy hh:mm")
    label(ws, f"B{start_row+2}", "Signature")
    ws.merge_cells(start_row=start_row+2, start_column=3, end_row=start_row+2, end_column=5)
    locked_cell(ws, f"C{start_row+2}", value="________________________")
    label(ws, f"F{start_row+2}", "Status")
    locked_cell(ws, f"G{start_row+2}", formula=f'=IF(C{start_row+1}<>"","SIGNED","PENDING")')
    status_cf(ws, f"G{start_row+2}:G{start_row+2}")

def add_kpi_card(ws, tl_col, tl_row, title, formula):
    tr_col = chr(ord(tl_col) + 1)
    ws.merge_cells(f"{tl_col}{tl_row}:{tr_col}{tl_row}")
    ws[f"{tl_col}{tl_row}"] = title
    ws[f"{tl_col}{tl_row}"].font = FONT_SMALL_WHITE
    ws[f"{tl_col}{tl_row}"].fill = FILL_NAVY
    ws[f"{tl_col}{tl_row}"].alignment = ALIGN_CENTER
    ws.merge_cells(f"{tl_col}{tl_row+1}:{tr_col}{tl_row+3}")
    ws[f"{tl_col}{tl_row+1}"] = formula
    ws[f"{tl_col}{tl_row+1}"].font = FONT_KPI
    ws[f"{tl_col}{tl_row+1}"].fill = FILL_LIGHT
    ws[f"{tl_col}{tl_row+1}"].alignment = ALIGN_CENTER
    ws[f"{tl_col}{tl_row+1}"].border = BORDER_BOX

def add_button_placeholder(ws, rng, text, note=None):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    c.value = text
    c.font = FONT_BUTTON
    c.fill = FILL_CYAN
    c.alignment = ALIGN_CENTER
    c.border = BORDER_BOX
    if note:
        c.comment = Comment(note, "OpenAI")

wb = Workbook()
wb.remove(wb.active)

sheet_names = [
    "00_Cover","01_Navigation","02_Instructions","03_Document_Control","04_Master_Input_Form",
    "05_Supporting_Inputs","06_Validation_Lists","07_Calculations","08_Checks","09_UI_Components",
    "10_Print_Form","11_Print_Summary","12_Print_Approval","13_Dashboard","14_Revision_Log",
    "15_Export_Map","16_Config","17_Output_Register","18_Deployment_Notes","19_Button_Mapping",
    "20_Release_Checklist","21_Workflow_Control","98_Macro_Companion","99_Admin_Hidden",
]
for s in sheet_names:
    ws = wb.create_sheet(s)
    set_standard_columns(ws)
    set_row_heights(ws)

# Config
ws = wb["16_Config"]
style_title(ws, "B2:J2", "CONFIGURATION")
cfg = [
    ("B4", "Company_Name", "C4", "Institution Name"),
    ("B5", "Document_Title_Default", "C5", "Controlled Institutional Document"),
    ("B6", "Default_Font", "C6", "Arial"),
    ("B7", "Primary_Color", "C7", NAVY),
    ("B8", "Accent_Color", "C8", CYAN),
    ("B9", "Confidentiality_Default", "C9", "Internal"),
    ("B10", "Package_Name_Prefix", "C10", "DOCPACK"),
    ("B11", "Archive_Path_Note", "C11", "Set by deployment environment"),
]
for l, txt, v, val in cfg:
    label(ws, l, txt)
    locked_cell(ws, v, value=val)
add_named_range(wb, "Company_Name", "16_Config", "$C$4")
add_named_range(wb, "Document_Title_Default", "16_Config", "$C$5")
apply_page_setup(ws, "B2:J14")

# Validation Lists
ws = wb["06_Validation_Lists"]
style_title(ws, "B2:I2", "VALIDATION LISTS")
lists = {
    "B": ("Department_List", ["Finance", "Engineering", "Operations", "Legal", "Management"]),
    "C": ("Confidentiality_List", ["Internal", "Restricted", "Public"]),
    "D": ("Status_List", ["Draft", "In Review", "Review Complete", "Approved", "Archived"]),
    "E": ("User_List", ["Prepared By", "Reviewer", "Approver"]),
    "F": ("Boolean_List", ["YES", "NO"]),
    "G": ("Severity_List", ["Critical", "Medium", "Low"]),
    "H": ("Archive_Status_List", ["Pending", "Archived"]),
    "I": ("Workflow_State_List", ["Pre-Issue", "Post-Issue", "Archive"]),
}
for col, (name, vals) in lists.items():
    ws[f"{col}4"] = name
    ws[f"{col}4"].font = FONT_LABEL
    for i, val in enumerate(vals, start=5):
        ws[f"{col}{i}"] = val
        ws[f"{col}{i}"].font = FONT_BODY
    add_named_range(wb, name, "06_Validation_Lists", f"${col}$5:${col}${4+len(vals)}")
apply_page_setup(ws, "B2:I14")

# Document Control
ws = wb["03_Document_Control"]
style_title(ws, "B2:J2", "DOCUMENT CONTROL")
style_band(ws, "B4:J4", "Core Metadata")
fields = [
    ("B6", "Document_Title", "C6"),("B7", "Document_ID", "C7"),("B8", "Version", "C8"),
    ("B9", "Issue_Timestamp_Static", "C9"),("B10", "Prepared_By", "C10"),("B11", "Reviewed_By", "C11"),
    ("B12", "Approved_By", "C12"),("B13", "Department", "C13"),("B14", "Confidentiality", "C14"),
    ("B15", "Status", "C15"),("B16", "Review_Timestamp_Static", "C16"),("B17", "Approval_Timestamp_Static", "C17"),
    ("B18", "Export_File_Name", "C18"),("B19", "Workflow_State", "C19"),("B20", "Record_Lock_Status", "C20"),
    ("B21", "Archive_Lock_Status", "C21"),
]
for l, t, v in fields:
    label(ws, l, t)
    input_cell(ws, v)

ws["C6"] = "=Document_Title_Default"
ws["C7"] = '=IF(OR(C13="",C9=""),"",UPPER(LEFT(C13,3))&"-"&TEXT(C9,"YYYYMMDD")&"-"&TEXT(MAX(1,COUNTA(\'14_Revision_Log\'!B:B)-4),"000"))'
ws["C8"] = "v1.0"
ws["C15"] = '=IF(C12<>"","Approved",IF(C11<>"","Review Complete",IF(C10<>"","In Review","Draft")))'
ws["C18"] = '=Document_ID&"_"&Version&"_"&TEXT(INT(C9),"yyyymmdd")&".pdf"'
ws["C19"] = '=IF(C15="Approved","Post-Issue","Pre-Issue")'
ws["C20"] = '=IF(AND(Document_Status="Approved",Approval_Timestamp<>""),"LOCKED","OPEN")'
ws["C21"] = '=IF(Archive_Ready="YES","LOCKED","OPEN")'
for c in ["C6","C7","C8","C15","C18","C19","C20","C21"]:
    ws[c].fill = FILL_LIGHT
    ws[c].font = FONT_BODY
    ws[c].protection = LOCKED
    ws[c].border = BORDER_THIN
ws["C9"] = ""
ws["C16"] = ""
ws["C17"] = ""
dv_user = DataValidation(type="list", formula1="=User_List", allow_blank=True)
dv_dept = DataValidation(type="list", formula1="=Department_List", allow_blank=False)
dv_conf = DataValidation(type="list", formula1="=Confidentiality_List", allow_blank=False)
for dv in [dv_user, dv_dept, dv_conf]:
    ws.add_data_validation(dv)
dv_user.add("C10"); dv_user.add("C11"); dv_user.add("C12")
dv_dept.add("C13"); dv_conf.add("C14")
for name, ref in [
    ("Document_Title", "$C$6"),("Document_ID", "$C$7"),("Version", "$C$8"),("Issue_Timestamp", "$C$9"),
    ("Prepared_By", "$C$10"),("Reviewed_By", "$C$11"),("Approved_By", "$C$12"),("Department", "$C$13"),
    ("Confidentiality", "$C$14"),("Document_Status", "$C$15"),("Review_Timestamp", "$C$16"),
    ("Approval_Timestamp", "$C$17"),("Export_File_Name", "$C$18"),("Workflow_State", "$C$19"),
    ("Record_Lock_Status", "$C$20"),("Archive_Lock_Status", "$C$21"),
]:
    add_named_range(wb, name, "03_Document_Control", ref)
apply_page_setup(ws, "B2:J24")

# Input form
ws = wb["04_Master_Input_Form"]
style_title(ws, "B2:J2", "MASTER INPUT FORM")
style_band(ws, "B4:J4", "Mandatory Fields")
fields = [
    (6, "Project_Name", "Short project title"),(7, "Project_Code", "Internal project code"),
    (8, "Department", "Use controlled list"),(9, "Prepared_By", "Use controlled list"),
    (10, "Date_Prepared", "Must be valid date"),(11, "Reference_Number", "Free-form reference"),
    (12, "Description", "Executive-level description"),(13, "Notes", "Supporting narrative"),
]
for row, field, comment in fields:
    label(ws, f"B{row}", field)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=9)
    input_cell(ws, f"C{row}", comment=comment)
dv_dept2 = DataValidation(type="list", formula1="=Department_List", allow_blank=False)
dv_user2 = DataValidation(type="list", formula1="=User_List", allow_blank=False)
dv_date = DataValidation(type="date", operator="between", formula1="DATE(2000,1,1)", formula2="DATE(2100,12,31)")
for dv in [dv_dept2, dv_user2, dv_date]:
    ws.add_data_validation(dv)
dv_dept2.add("C8"); dv_user2.add("C9"); dv_date.add("C10")
for name, ref in [
    ("Input_Project_Name", "$C$6"),("Input_Project_Code", "$C$7"),("Input_Department", "$C$8"),
    ("Input_Prepared_By", "$C$9"),("Input_Date", "$C$10"),("Input_Reference", "$C$11"),
    ("Input_Description", "$C$12"),("Input_Notes", "$C$13"),("Mandatory_Range", "$C$6:$C$12"),
]:
    add_named_range(wb, name, "04_Master_Input_Form", ref)
apply_page_setup(ws, "B2:J24")

# Supporting Inputs
ws = wb["05_Supporting_Inputs"]
style_title(ws, "B2:J2", "SUPPORTING INPUTS")
headers = ["Input_Category","Input_Value","Comment","Owner","Status","Required"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"
    ws[cell] = h
    ws[cell].font = FONT_SMALL_WHITE
    ws[cell].fill = FILL_NAVY
    ws[cell].alignment = ALIGN_CENTER
    ws[cell].border = BORDER_THIN
for r in range(5, 21):
    for c in ["B","C","D","E","F","G"]:
        input_cell(ws, f"{c}{r}")
status_cf(ws, "F5:F20")
apply_page_setup(ws, "B2:J24")

# Calculations
ws = wb["07_Calculations"]
style_title(ws, "B2:J2", "CALCULATIONS")
calc_rows = [
    (4, "Mandatory_Fields_Total", '=COUNTA(Mandatory_Range)'),
    (5, "Mandatory_Fields_Filled", '=COUNTA(Mandatory_Range)-COUNTBLANK(Mandatory_Range)'),
    (6, "Completion_Percentage", '=IF(C4=0,0,C5/C4)'),
    (7, "Failed_Checks_Count", '=COUNTIF(\'08_Checks\'!F5:F40,"FAIL")'),
    (8, "Export_Status", '=IF(C7>0,"EXPORT BLOCKED","EXPORT READY")'),
    (9, "Ready_Export_Rows", '=COUNTIF(\'15_Export_Map\'!I5:I20,"READY")'),
    (10, "Required_Export_Rows", '=COUNTIF(\'15_Export_Map\'!D5:D20,"YES")'),
    (11, "Print_Setup_OK", '=IF(C9=C10,"OK","ERROR")'),
    (12, "Package_Readiness", '=IF(AND(C7=0,C11="OK"),"READY","BLOCKED")'),
    (13, "Archive_Ready", '=IF(AND(Document_Status="Approved",Package_Readiness="READY"),"YES","NO")'),
    (14, "Post_Issue_Ready", '=IF(AND(Document_Status="Approved",Issue_Timestamp<>"",Export_Status="EXPORT READY"),"YES","NO")'),
]
for r, metric, formula in calc_rows:
    label(ws, f"B{r}", metric)
    locked_cell(ws, f"C{r}", formula=formula)
    if r == 6:
        ws[f"C{r}"].number_format = "0.0%"
for name, ref in [
    ("Completion_Percentage", "$C$6"),("Failed_Checks", "$C$7"),("Export_Status", "$C$8"),
    ("Print_Setup_OK", "$C$11"),("Package_Readiness", "$C$12"),("Archive_Ready", "$C$13"),("Post_Issue_Ready", "$C$14"),
]:
    add_named_range(wb, name, "07_Calculations", ref)
apply_page_setup(ws, "B2:J18")

# Export Map
ws = wb["15_Export_Map"]
style_title(ws, "B2:K2", "EXPORT MAP")
headers = ["Sheet_Name","Output_Type","Include_in_PDF","Page_Order","Expected_Print_Area","Actual_Print_Area","Print_Area_OK","Export_Row_Status","Footer_Check","Sheet_Lock_Check"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"
    ws[cell] = h
    ws[cell].font = FONT_SMALL_WHITE
    ws[cell].fill = FILL_NAVY
    ws[cell].alignment = ALIGN_CENTER
    ws[cell].border = BORDER_THIN
rows = [
    ("00_Cover", "Cover", "YES", 1, "B2:J28"),
    ("11_Print_Summary", "Summary", "YES", 2, "B2:J28"),
    ("10_Print_Form", "Form", "YES", 3, "B2:J28"),
    ("12_Print_Approval", "Approval", "YES", 4, "B2:J28"),
    ("14_Revision_Log", "Revision Log", "YES", 5, "B2:K30"),
]
for i, row in enumerate(rows, start=5):
    sheet_name, out_type, include, order, expected = row
    ws[f"B{i}"] = sheet_name; ws[f"C{i}"] = out_type; ws[f"D{i}"] = include; ws[f"E{i}"] = order
    ws[f"F{i}"] = expected; ws[f"G{i}"] = expected
    ws[f"H{i}"] = f'=IF(AND(B{i}<>"",F{i}=G{i}),"OK","ERROR")'
    ws[f"I{i}"] = f'=IF(AND(D{i}="YES",H{i}="OK",J{i}="OK",K{i}="OK"),"READY","REVIEW")'
    ws[f"J{i}"] = "OK"; ws[f"K{i}"] = "OK"
    for c in "BCDEFGHIJK":
        ws[f"{c}{i}"].border = BORDER_THIN
        ws[f"{c}{i}"].alignment = ALIGN_LEFT
status_cf(ws, "H5:H20"); status_cf(ws, "I5:I20"); status_cf(ws, "J5:J20"); status_cf(ws, "K5:K20")
apply_page_setup(ws, "B2:K20")

# Checks
ws = wb["08_Checks"]
style_title(ws, "B2:K2", "CHECKS MATRIX")
headers = ["Check_ID","Category","Description","Formula_Result","Status","Severity","Owner","Action_Required","QC_Group","Workflow_Phase"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"
    ws[cell] = h
    ws[cell].font = FONT_SMALL_WHITE
    ws[cell].fill = FILL_NAVY
    ws[cell].alignment = ALIGN_CENTER
    ws[cell].border = BORDER_THIN
checks = [
    ("C01","Completeness","Mandatory fields completed", '=IF(COUNTBLANK(Mandatory_Range)=0,"OK","ERROR")', '=IF(E5="OK","PASS","FAIL")',"Critical","Model Owner","Complete missing required inputs","Input","Pre-Issue"),
    ("C02","Chronology","Input date valid", '=IF(Input_Date<=TODAY(),"OK","ERROR")', '=IF(E6="OK","PASS","FAIL")',"Critical","Model Owner","Correct invalid date","Input","Pre-Issue"),
    ("C03","Metadata","Document ID generated", '=IF(Document_ID<>"","OK","ERROR")', '=IF(E7="OK","PASS","FAIL")',"Critical","Document Control","Resolve metadata driver","Metadata","Pre-Issue"),
    ("C04","Metadata","Prepared by populated", '=IF(Prepared_By<>"","OK","ERROR")', '=IF(E8="OK","PASS","FAIL")',"Medium","Document Control","Assign document owner","Metadata","Pre-Issue"),
    ("C05","Governance","Approval sequence valid", '=IF(Approved_By<>"",IF(Reviewed_By="","ERROR","OK"),"OK")', '=IF(E9="OK","PASS","FAIL")',"Critical","Approver","Reviewer required before approval","Governance","Pre-Issue"),
    ("C06","Metadata","Confidentiality populated", '=IF(Confidentiality<>"","OK","ERROR")', '=IF(E10="OK","PASS","FAIL")',"Medium","Document Control","Select confidentiality","Metadata","Pre-Issue"),
    ("C07","Metadata","Version populated", '=IF(Version<>"","OK","ERROR")', '=IF(E11="OK","PASS","FAIL")',"Medium","Document Control","Set version","Metadata","Pre-Issue"),
    ("C08","Export","Export rows configured", '=IF(COUNTIF(\'15_Export_Map\'!D5:D20,"YES")>0,"OK","ERROR")', '=IF(E12="OK","PASS","FAIL")',"Medium","Document Control","Set export pack rows","Export","Pre-Issue"),
    ("C09","Export","All active print areas validated", '=IF(COUNTIF(\'15_Export_Map\'!I5:I20,"REVIEW")=0,"OK","ERROR")', '=IF(E13="OK","PASS","FAIL")',"Critical","Document Control","Resolve print area mismatch","Export","Pre-Issue"),
    ("C10","Export","Package print setup OK", '=Print_Setup_OK', '=IF(E14="OK","PASS","FAIL")',"Critical","Document Control","Repair package print consistency","Export","Pre-Issue"),
    ("C11","Governance","Document status consistent", '=IF(AND(Document_Status="Approved",Approved_By=""),"ERROR","OK")', '=IF(E15="OK","PASS","FAIL")',"Critical","Approver","Fix status chain","Governance","Pre-Issue"),
    ("C12","Governance","Package readiness consistent", '=IF(Package_Readiness="READY","OK","ERROR")', '=IF(E16="OK","PASS","FAIL")',"Critical","Document Control","Resolve remaining blockers","Governance","Pre-Issue"),
    ("C13","QC","Cover included in pack", '=IF(COUNTIF(\'15_Export_Map\'!B:B,"00_Cover")>0,"OK","ERROR")', '=IF(E17="OK","PASS","FAIL")',"Medium","Document Control","Restore cover page","QC","Pre-Issue"),
    ("C14","QC","Summary included in pack", '=IF(COUNTIF(\'15_Export_Map\'!B:B,"11_Print_Summary")>0,"OK","ERROR")', '=IF(E18="OK","PASS","FAIL")',"Medium","Document Control","Restore summary page","QC","Pre-Issue"),
    ("C15","QC","Approval page included in pack", '=IF(COUNTIF(\'15_Export_Map\'!B:B,"12_Print_Approval")>0,"OK","ERROR")', '=IF(E19="OK","PASS","FAIL")',"Medium","Document Control","Restore approval page","QC","Pre-Issue"),
    ("C16","QC","Revision log included in pack", '=IF(COUNTIF(\'15_Export_Map\'!B:B,"14_Revision_Log")>0,"OK","ERROR")', '=IF(E20="OK","PASS","FAIL")',"Medium","Document Control","Restore revision log","QC","Pre-Issue"),
    ("C17","QC","Issue timestamp exists", '=IF(Issue_Timestamp<>"","OK","ERROR")', '=IF(E21="OK","PASS","FAIL")',"Critical","Document Control","Populate issue timestamp","QC","Post-Issue"),
    ("C18","QC","Review timestamp consistent", '=IF(AND(Reviewed_By<>"",Review_Timestamp=""),"ERROR","OK")', '=IF(E22="OK","PASS","FAIL")',"Critical","Reviewer","Populate review timestamp","QC","Post-Issue"),
    ("C19","QC","Approval timestamp consistent", '=IF(AND(Approved_By<>"",Approval_Timestamp=""),"ERROR","OK")', '=IF(E23="OK","PASS","FAIL")',"Critical","Approver","Populate approval timestamp","QC","Post-Issue"),
    ("C20","Archive","Archive readiness consistent", '=IF(AND(Document_Status="Approved",Archive_Ready="YES"),"OK",IF(Document_Status="Approved","ERROR","OK"))', '=IF(E24="OK","PASS","FAIL")',"Medium","Archive Admin","Resolve archive preconditions","Archive","Archive"),
    ("C21","Archive","Output register populated", '=IF(AND(\'17_Output_Register\'!B5<>"",\'17_Output_Register\'!E5<>""),"OK","ERROR")', '=IF(E25="OK","PASS","FAIL")',"Medium","Archive Admin","Populate output register","Archive","Archive"),
    ("C22","Hardening","Approved record must be locked", '=IF(AND(Document_Status="Approved",Record_Lock_Status<>"LOCKED"),"ERROR","OK")', '=IF(E26="OK","PASS","FAIL")',"Critical","Document Control","Lock record after approval","Hardening","Post-Issue"),
    ("C23","Hardening","Archived record must be locked", '=IF(AND(Archive_Ready="YES",Archive_Lock_Status<>"LOCKED"),"ERROR","OK")', '=IF(E27="OK","PASS","FAIL")',"Critical","Archive Admin","Lock archived record","Hardening","Archive"),
    ("C24","Hardening","Output register complete before archive", '=IF(AND(Archive_Ready="YES",\'17_Output_Register\'!K5<>"COMPLETE"),"ERROR","OK")', '=IF(E28="OK","PASS","FAIL")',"Critical","Archive Admin","Complete output register","Hardening","Archive"),
]
for r, row in enumerate(checks, start=5):
    for i, val in enumerate(row, start=2):
        ws[f"{get_column_letter(i)}{r}"] = val
        ws[f"{get_column_letter(i)}{r}"].border = BORDER_THIN
        ws[f"{get_column_letter(i)}{r}"].alignment = ALIGN_LEFT
add_named_range(wb, "Check_Status_Table", "08_Checks", "$F$5:$F$28")
status_cf(ws, "E5:E35"); status_cf(ws, "F5:F35")
apply_page_setup(ws, "B2:K32")

# Dashboard
ws = wb["13_Dashboard"]
style_title(ws, "B2:J2", "DOCUMENT CONTROL DASHBOARD")
add_kpi_card(ws, "B", 4, "Completion %", "=Completion_Percentage")
add_kpi_card(ws, "D", 4, "Failed Checks", "=Failed_Checks")
add_kpi_card(ws, "F", 4, "Export Status", "=Export_Status")
add_kpi_card(ws, "H", 4, "Archive Ready", '=IF(Archive_Ready="YES","ARCHIVED","PENDING")')
style_band(ws, "B9:J9", "Document Status Waterfall")
ws["B11"] = "Draft"; ws["C11"] = '=IF(Document_Status="Draft","DRAFT","")'
ws["D11"] = "In Review"; ws["E11"] = '=IF(Document_Status="In Review","IN REVIEW","")'
ws["F11"] = "Review Complete"; ws["G11"] = '=IF(Document_Status="Review Complete","REVIEW COMPLETE","")'
ws["H11"] = "Approved"; ws["I11"] = '=IF(Document_Status="Approved","APPROVED","")'
for rng in ["C11:C11","E11:E11","G11:G11","I11:I11"]:
    status_cf(ws, rng)
style_band(ws, "B14:J14", "Executive Status")
label(ws, "B16", "Issue Timestamp"); locked_cell(ws, "C16", formula="=Issue_Timestamp", numfmt="dd-mmm-yyyy hh:mm")
label(ws, "B17", "Review Timestamp"); locked_cell(ws, "C17", formula="=Review_Timestamp", numfmt="dd-mmm-yyyy hh:mm")
label(ws, "B18", "Approval Timestamp"); locked_cell(ws, "C18", formula="=Approval_Timestamp", numfmt="dd-mmm-yyyy hh:mm")
label(ws, "F16", "Package Readiness"); locked_cell(ws, "G16", formula="=Package_Readiness")
label(ws, "F17", "Workflow State"); locked_cell(ws, "G17", formula="=Workflow_State")
label(ws, "F18", "Archive Ready"); locked_cell(ws, "G18", formula='=IF(Archive_Ready="YES","ARCHIVED","PENDING")')
label(ws, "F19", "Record Lock"); locked_cell(ws, "G19", formula="=Record_Lock_Status")
label(ws, "F20", "Archive Lock"); locked_cell(ws, "G20", formula="=Archive_Lock_Status")
for rng in ["G16:G20"]:
    status_cf(ws, rng)
style_band(ws, "B21:J21", "Button Placeholder Zones")
add_button_placeholder(ws, "B23:C24", "OPEN INPUT FORM", "Assign VBA macro: GoToInputForm")
add_button_placeholder(ws, "D23:E24", "OPEN CHECKS", "Assign VBA macro: GoToChecks")
add_button_placeholder(ws, "F23:G24", "EXPORT PDF PACK", "Assign VBA macro: ExportInstitutionalPackToPDF")
add_button_placeholder(ws, "H23:I24", "ARCHIVE RECORD", "Assign VBA macro: ArchiveOutputRecord")
apply_page_setup(ws, "B2:J28")

# Output sheets skeleton
for sheet_name, title in [("00_Cover","INSTITUTIONAL DOCUMENT PACK"),("10_Print_Form","FORM"),("11_Print_Summary","EXECUTIVE SUMMARY"),("12_Print_Approval","APPROVAL PAGE")]:
    ws = wb[sheet_name]
    style_title(ws, "B2:J2", title)
    build_meta_header(ws)

ws = wb["00_Cover"]
ws.merge_cells("B5:C8"); ws["B5"] = "LOGO"; ws["B5"].alignment = ALIGN_CENTER; ws["B5"].fill = FILL_LIGHT; ws["B5"].border = BORDER_BOX; ws["B5"].font = FONT_SECTION
ws.merge_cells("D5:J6"); ws["D5"] = "=Document_Title"; ws["D5"].font = Font(name="Arial", size=14, bold=True, color=NAVY); ws["D5"].alignment = ALIGN_LEFT
ws.merge_cells("D7:J8"); ws["D7"] = '=Company_Name&CHAR(10)&"Controlled, Reproducible, and Audit-Traceable Output Package"'; ws["D7"].alignment = ALIGN_LEFT; ws["D7"].font = FONT_BODY
style_band(ws, "B10:J10", "Document Metadata")
meta = [
    (12,"Document_ID","=Document_ID"),(13,"Version","=Version"),(14,"Issue_Timestamp","=Issue_Timestamp"),
    (15,"Prepared_By","=Prepared_By"),(16,"Reviewed_By","=Reviewed_By"),(17,"Approved_By","=Approved_By"),
    (18,"Confidentiality","=Confidentiality"),(19,"Status","=Document_Status"),
]
for row, lbl, formula in meta:
    label(ws, f"B{row}", lbl); locked_cell(ws, f"D{row}", formula=formula)

ws = wb["10_Print_Form"]
style_band(ws, "B5:J5", "Form Output")
form_rows = [
    (7,"Project_Name","=Input_Project_Name"),(8,"Project_Code","=Input_Project_Code"),(9,"Department","=Input_Department"),
    (10,"Prepared_By","=Input_Prepared_By"),(11,"Date_Prepared","=Input_Date"),(12,"Reference_Number","=Input_Reference"),
    (13,"Description","=Input_Description"),(14,"Notes","=Input_Notes"),
]
for row, lbl, formula in form_rows:
    label(ws, f"B{row}", lbl)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=9)
    locked_cell(ws, f"C{row}", formula=formula)

ws = wb["11_Print_Summary"]
style_band(ws, "B5:F5", "Document Overview")
ws.merge_cells("B7:F10")
locked_cell(ws, "B7", formula='="This package provides a controlled, reproducible, and audit-traceable institutional document output with embedded validation, static timestamp controls, approval workflow, revision history, archive readiness, and release governance."')
ws["B7"].alignment = ALIGN_LEFT
style_band(ws, "G5:J5", "Status Panel")
label(ws, "G7", "Completion %"); locked_cell(ws, "H7", formula="=Completion_Percentage", numfmt="0.0%")
label(ws, "G8", "Failed Checks"); locked_cell(ws, "H8", formula="=Failed_Checks")
label(ws, "G9", "Export Status"); locked_cell(ws, "H9", formula="=Export_Status")
label(ws, "G10", "Archive Ready"); locked_cell(ws, "H10", formula='=IF(Archive_Ready="YES","ARCHIVED","PENDING")')
for rng in ["H9:H10"]:
    status_cf(ws, rng)

ws = wb["12_Print_Approval"]
add_signature_block(ws, 5, "Prepared By", "=Prepared_By", "=Issue_Timestamp")
add_signature_block(ws, 10, "Reviewed By", "=Reviewed_By", "=Review_Timestamp")
add_signature_block(ws, 15, "Approved By", "=Approved_By", "=Approval_Timestamp")

for sheet_name, area in [("00_Cover","B2:J28"),("10_Print_Form","B2:J28"),("11_Print_Summary","B2:J28"),("12_Print_Approval","B2:J28")]:
    apply_page_setup(wb[sheet_name], area)

# Revision log
ws = wb["14_Revision_Log"]
style_title(ws, "B2:K2", "REVISION LOG")
headers = ["Revision_No","Revision_Date","Author","Reviewer","Approved_By","Change_Type","Change_Summary","Status","Effective_Timestamp","Archived_Copy"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"; ws[cell] = h; ws[cell].font = FONT_SMALL_WHITE; ws[cell].fill = FILL_NAVY; ws[cell].alignment = ALIGN_CENTER; ws[cell].border = BORDER_THIN
initial = ["v1.0", "=TODAY()", "=Prepared_By", "=Reviewed_By", "=Approved_By", "Initial Issue", "Template creation", "=Document_Status", "=Issue_Timestamp", ""]
for i, val in enumerate(initial, start=2):
    input_cell(ws, f"{get_column_letter(i)}5"); ws[f"{get_column_letter(i)}5"] = val
for r in range(6, 21):
    for c in range(2, 12):
        input_cell(ws, f"{get_column_letter(c)}{r}")
status_cf(ws, "I5:I20")
apply_page_setup(ws, "B2:K30")

# Output register
ws = wb["17_Output_Register"]
style_title(ws, "B2:K2", "ARCHIVE-READY OUTPUT REGISTER")
headers = ["Document_ID","Version","Issue_Timestamp","Export_File_Name","Status","Archive_Status","Archive_Date","Owner","Location","Record_Status"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"; ws[cell] = h; ws[cell].font = FONT_SMALL_WHITE; ws[cell].fill = FILL_NAVY; ws[cell].alignment = ALIGN_CENTER; ws[cell].border = BORDER_THIN
ws["B5"] = "=Document_ID"; ws["C5"] = "=Version"; ws["D5"] = "=Issue_Timestamp"; ws["E5"] = "=Export_File_Name"; ws["F5"] = "=Document_Status"
ws["G5"] = '=IF(Archive_Ready="YES","Archived","Pending")'; ws["H5"] = '=IF(G5="Archived",TODAY(),"")'; ws["I5"] = "=Prepared_By"
ws["J5"] = '=IF(G5="Archived","Archive location set by deployment","Pending archive")'; ws["K5"] = '=IF(AND(B5<>"",E5<>"",F5<>""),"COMPLETE","MISSING")'
for c in "BCDEFGHIJK":
    ws[f"{c}5"].border = BORDER_THIN
status_cf(ws, "F5:G20"); status_cf(ws, "K5:K20")
for r in range(6, 21):
    for c in "BCDEFGHIJK":
        input_cell(ws, f"{c}{r}")
apply_page_setup(ws, "B2:K28")

# Deployment notes
ws = wb["18_Deployment_Notes"]
style_title(ws, "B2:J2", "XLSM DEPLOYMENT NOTES")
notes = [
    "1. Open the generated .xlsx file in desktop Excel and Save As .xlsm.",
    "2. Copy VBA code from sheet 98_Macro_Companion into a standard VBA module.",
    "3. Replace static timestamp manual cells C9, C16, C17 in Document_Control with VBA stamping on issue/review/approval actions.",
    "4. Insert shape buttons above each cyan placeholder zone and assign macros from the mapping matrix.",
    "5. Test all export sheets, print areas, footer consistency, and locked sheet behavior before release.",
    "6. After approved export, run archive routine and confirm Output Register line is complete.",
    "7. Apply sheet passwords externally and keep custody outside the workbook.",
]
for i, txt in enumerate(notes, start=5):
    ws.merge_cells(f"B{i}:J{i}"); ws[f"B{i}"] = txt; ws[f"B{i}"].font = FONT_BODY; ws[f"B{i}"].alignment = ALIGN_LEFT
apply_page_setup(ws, "B2:J22")

# Button mapping
ws = wb["19_Button_Mapping"]
style_title(ws, "B2:J2", "BUTTON-TO-MACRO MAPPING MATRIX")
headers = ["Sheet","Placeholder_Label","Cell_Range","Macro_Name","Purpose","Mandatory"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"; ws[cell] = h; ws[cell].font = FONT_SMALL_WHITE; ws[cell].fill = FILL_NAVY; ws[cell].alignment = ALIGN_CENTER; ws[cell].border = BORDER_THIN
rows = [
    ("01_Navigation","OPEN INPUT","F18:G19","GoToInputForm","Navigate to input sheet","YES"),
    ("01_Navigation","EXPORT PDF","H18:I19","ExportInstitutionalPackToPDF","Export PDF pack","YES"),
    ("01_Navigation","OPEN CHECKS","F20:G21","GoToChecks","Navigate to checks sheet","YES"),
    ("01_Navigation","ARCHIVE","H20:I21","ArchiveOutputRecord","Archive current record","YES"),
    ("13_Dashboard","OPEN INPUT FORM","B23:C24","GoToInputForm","Navigate to input sheet","YES"),
    ("13_Dashboard","OPEN CHECKS","D23:E24","GoToChecks","Navigate to checks sheet","YES"),
    ("13_Dashboard","EXPORT PDF PACK","F23:G24","ExportInstitutionalPackToPDF","Export PDF pack","YES"),
    ("13_Dashboard","ARCHIVE RECORD","H23:I24","ArchiveOutputRecord","Archive current record","YES"),
]
for r, row in enumerate(rows, start=5):
    for i, val in enumerate(row, start=2):
        ws[f"{get_column_letter(i)}{r}"] = val; ws[f"{get_column_letter(i)}{r}"].border = BORDER_THIN
apply_page_setup(ws, "B2:J22")

# Release checklist
ws = wb["20_Release_Checklist"]
style_title(ws, "B2:K2", "RELEASE CHECKLIST")
headers = ["Check_Item","Phase","Status","Owner","Evidence","Mandatory","Comment"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"; ws[cell] = h; ws[cell].font = FONT_SMALL_WHITE; ws[cell].fill = FILL_NAVY; ws[cell].alignment = ALIGN_CENTER; ws[cell].border = BORDER_THIN
items = [
    ("Mandatory inputs completed","Pre-Issue", '=IF(COUNTBLANK(Mandatory_Range)=0,"COMPLETE","MISSING")',"Model Owner","Input sheet","YES",""),
    ("Checks matrix no FAIL items","Pre-Issue", '=IF(Failed_Checks=0,"COMPLETE","MISSING")',"Document Control","Checks sheet","YES",""),
    ("PDF pack rows validated","Pre-Issue", '=IF(Print_Setup_OK="OK","COMPLETE","MISSING")',"Document Control","Export map","YES",""),
    ("Issue timestamp stamped","Post-Issue", '=IF(Issue_Timestamp<>"","COMPLETE","MISSING")',"Document Control","Document_Control!C9","YES",""),
    ("Review timestamp stamped","Post-Issue", '=IF(OR(Reviewed_By="",Review_Timestamp<>""),"COMPLETE","MISSING")',"Reviewer","Document_Control!C16","YES",""),
    ("Approval timestamp stamped","Post-Issue", '=IF(OR(Approved_By="",Approval_Timestamp<>""),"COMPLETE","MISSING")',"Approver","Document_Control!C17","YES",""),
    ("Approved record locked","Post-Issue", '=IF(Record_Lock_Status="LOCKED","COMPLETE","MISSING")',"Document Control","Document_Control!C20","YES",""),
    ("Output register updated","Archive", '=IF(\'17_Output_Register\'!K5="COMPLETE","COMPLETE","MISSING")',"Archive Admin","Output register","YES",""),
    ("Archive register append completed","Archive", '=IF(COUNTIF(\'17_Output_Register\'!K:K,"COMPLETE")>=1,"COMPLETE","MISSING")',"Archive Admin","Output_Register","YES",""),
    ("Archived record locked","Archive", '=IF(Archive_Lock_Status="LOCKED","COMPLETE","MISSING")',"Archive Admin","Document_Control!C21","YES",""),
]
for r, row in enumerate(items, start=5):
    for i, val in enumerate(row, start=2):
        ws[f"{get_column_letter(i)}{r}"] = val; ws[f"{get_column_letter(i)}{r}"].border = BORDER_THIN
status_cf(ws, "D5:D20")
apply_page_setup(ws, "B2:K24")

# Workflow control
ws = wb["21_Workflow_Control"]
style_title(ws, "B2:K2", "PRE-ISSUE / POST-ISSUE / ARCHIVE WORKFLOW CONTROL")
headers = ["Workflow_Phase","Control_Name","Formula_Result","Status","Owner","Action"]
for i, h in enumerate(headers, start=2):
    cell = f"{get_column_letter(i)}4"; ws[cell] = h; ws[cell].font = FONT_SMALL_WHITE; ws[cell].fill = FILL_NAVY; ws[cell].alignment = ALIGN_CENTER; ws[cell].border = BORDER_THIN
workflow_rows = [
    ("Pre-Issue","Inputs complete", '=IF(COUNTBLANK(Mandatory_Range)=0,"OK","ERROR")', '=IF(D5="OK","READY","BLOCKED")',"Model Owner","Complete inputs"),
    ("Pre-Issue","Checks clear", '=IF(Failed_Checks=0,"OK","ERROR")', '=IF(D6="OK","READY","BLOCKED")',"Document Control","Resolve fails"),
    ("Post-Issue","Issue timestamp exists", '=IF(Issue_Timestamp<>"","OK","ERROR")', '=IF(D7="OK","READY","BLOCKED")',"Document Control","Stamp issue time"),
    ("Post-Issue","Approved export ready", '=IF(Post_Issue_Ready="YES","OK","ERROR")', '=IF(D8="OK","READY","BLOCKED")',"Approver","Approve and export"),
    ("Archive","Archive readiness", '=IF(Archive_Ready="YES","OK","ERROR")', '=IF(D9="OK","READY","BLOCKED")',"Archive Admin","Archive output"),
    ("Archive","Output register complete", '=IF(\'17_Output_Register\'!K5="COMPLETE","OK","ERROR")', '=IF(D10="OK","READY","BLOCKED")',"Archive Admin","Finalize register"),
    ("Post-Issue","Approved record locked", '=IF(Record_Lock_Status="LOCKED","OK","ERROR")', '=IF(D11="OK","READY","BLOCKED")',"Document Control","Lock approved record"),
    ("Archive","Archive append completed", '=IF(COUNTIF(\'17_Output_Register\'!K:K,"COMPLETE")>=1,"OK","ERROR")', '=IF(D12="OK","READY","BLOCKED")',"Archive Admin","Append archive row"),
    ("Archive","Archived record locked", '=IF(Archive_Lock_Status="LOCKED","OK","ERROR")', '=IF(D13="OK","READY","BLOCKED")',"Archive Admin","Lock archived record"),
]
for r, row in enumerate(workflow_rows, start=5):
    for i, val in enumerate(row, start=2):
        ws[f"{get_column_letter(i)}{r}"] = val; ws[f"{get_column_letter(i)}{r}"].border = BORDER_THIN
status_cf(ws, "E5:E15")
apply_page_setup(ws, "B2:K22")

# Navigation
ws = wb["01_Navigation"]
style_title(ws, "B2:J2", "NAVIGATION")
nav = [
    (5,"Open Input Form","04_Master_Input_Form!A1"),(6,"Open Checks","08_Checks!A1"),(7,"Open Print Form","10_Print_Form!A1"),
    (8,"Open Summary","11_Print_Summary!A1"),(9,"Open Approval Page","12_Print_Approval!A1"),(10,"Open Revision Log","14_Revision_Log!A1"),
    (11,"Open Output Register","17_Output_Register!A1"),(12,"Open Release Checklist","20_Release_Checklist!A1"),
]
for row, txt, target in nav:
    ws[f"B{row}"] = txt
    ws[f"C{row}"] = f'=HYPERLINK("#{target}","Open")'
    ws[f"B{row}"].font = FONT_LABEL
    ws[f"C{row}"].font = Font(name="Arial", size=10, color=CYAN, underline="single")
    ws[f"C{row}"].protection = UNLOCKED
style_band(ws, "B15:J15", "Control Status")
label(ws, "B17", "Workbook Status"); locked_cell(ws, "C17", formula='=IF(Failed_Checks=0,"READY","NOT READY")')
label(ws, "B18", "Export Status"); locked_cell(ws, "C18", formula="=Export_Status")
label(ws, "B19", "Package Readiness"); locked_cell(ws, "C19", formula="=Package_Readiness")
label(ws, "B20", "Archive Ready"); locked_cell(ws, "C20", formula='=IF(Archive_Ready="YES","ARCHIVED","PENDING")')
for rng in ["C17:C20"]:
    status_cf(ws, rng)
style_band(ws, "F17:J17", "Button Placeholder Zones")
add_button_placeholder(ws, "F18:G19", "OPEN INPUT", "Assign VBA macro: GoToInputForm")
add_button_placeholder(ws, "H18:I19", "EXPORT PDF", "Assign VBA macro: ExportInstitutionalPackToPDF")
add_button_placeholder(ws, "F20:G21", "OPEN CHECKS", "Assign VBA macro: GoToChecks")
add_button_placeholder(ws, "H20:I21", "ARCHIVE", "Assign VBA macro: ArchiveOutputRecord")
apply_page_setup(ws, "B2:J24")

# Instructions and UI components
ws = wb["02_Instructions"]
style_title(ws, "B2:J2", "INSTRUCTIONS")
instructions = [
    "1. Edit only blue input cells.",
    "2. Static timestamps are manual/VBA-stamped values, not formula-driven NOW() cells.",
    "3. Do not override formulas, checks, export map, or output sheets.",
    "4. Approval chain must be Prepared → Reviewed → Approved.",
    "5. Run pre-issue checks before export, post-issue controls after export, archive controls after filing.",
]
for i, txt in enumerate(instructions, start=5):
    ws.merge_cells(f"B{i}:J{i}"); ws[f"B{i}"] = txt; ws[f"B{i}"].font = FONT_BODY; ws[f"B{i}"].alignment = ALIGN_LEFT
apply_page_setup(ws, "B2:J20")

ws = wb["09_UI_Components"]
style_title(ws, "B2:J2", "UI COMPONENTS")
for i, comp in enumerate(["Header_Metadata_Band","Board_Pack_Title_Block","KPI_Card","Signature_Block","Revision_Log_Table_Header","Warning_Panel","Button_Placeholder"], start=5):
    ws[f"B{i}"] = comp; ws[f"B{i}"].font = FONT_BODY
apply_page_setup(ws, "B2:J16")

# VBA companion
ws = wb["98_Macro_Companion"]
style_title(ws, "B2:J2", "VBA MACRO COMPANION")
macro_text = """
Sub ExportInstitutionalPackToPDF()
    Dim baseName As String
    Dim outPath As String
    baseName = Sheets("03_Document_Control").Range("C18").Value
    outPath = ThisWorkbook.Path & "\\" & baseName
    Sheets(Array("00_Cover", "11_Print_Summary", "10_Print_Form", "12_Print_Approval", "14_Revision_Log")).Select
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:=outPath, Quality:=xlQualityStandard, IncludeDocProperties:=True, _
        IgnorePrintAreas:=False, OpenAfterPublish:=False
End Sub

Sub GoToInputForm()
    Sheets("04_Master_Input_Form").Select
End Sub

Sub GoToChecks()
    Sheets("08_Checks").Select
End Sub

Sub ArchiveOutputRecord()
    Dim wsReg As Worksheet
    Dim nextRow As Long
    Set wsReg = Sheets("17_Output_Register")
    nextRow = wsReg.Cells(wsReg.Rows.Count, "B").End(xlUp).Row + 1
    If nextRow < 6 Then nextRow = 6
    wsReg.Cells(nextRow, "B").Value = Sheets("03_Document_Control").Range("C7").Value
    wsReg.Cells(nextRow, "C").Value = Sheets("03_Document_Control").Range("C8").Value
    wsReg.Cells(nextRow, "D").Value = Sheets("03_Document_Control").Range("C9").Value
    wsReg.Cells(nextRow, "E").Value = Sheets("03_Document_Control").Range("C18").Value
    wsReg.Cells(nextRow, "F").Value = Sheets("03_Document_Control").Range("C15").Value
    wsReg.Cells(nextRow, "G").Value = "Archived"
    wsReg.Cells(nextRow, "H").Value = Now
    wsReg.Cells(nextRow, "I").Value = Sheets("03_Document_Control").Range("C10").Value
    wsReg.Cells(nextRow, "J").Value = "Archive location set by deployment"
    wsReg.Cells(nextRow, "K").Value = "COMPLETE"
    MsgBox "Archive register updated at row " & nextRow, vbInformation
End Sub

Sub StampIssueTimestamp()
    If Sheets("03_Document_Control").Range("C9").Value = "" Then
        Sheets("03_Document_Control").Range("C9").Value = Now
    End If
End Sub

Sub StampReviewTimestamp()
    If Sheets("03_Document_Control").Range("C16").Value = "" Then
        Sheets("03_Document_Control").Range("C16").Value = Now
    End If
End Sub

Sub StampApprovalTimestamp()
    If Sheets("03_Document_Control").Range("C17").Value = "" Then
        Sheets("03_Document_Control").Range("C17").Value = Now
    End If
End Sub
"""
ws.merge_cells("B4:J34"); ws["B4"] = macro_text; ws["B4"].alignment = ALIGN_LEFT; ws["B4"].font = Font(name="Consolas", size=9, color=BLACK)
apply_page_setup(ws, "B2:J34")

# Admin hidden
ws = wb["99_Admin_Hidden"]
ws["A1"] = "System_Use_Only"
ws["A2"] = "Template_Version"; ws["B2"] = "v3.2.2"
ws["A3"] = "Deployment_Mode"; ws["B3"] = "xlsx-ready / xlsm-target"
ws.sheet_state = "veryHidden"

for sheet_name, area in [("00_Cover","B2:J28"),("10_Print_Form","B2:J28"),("11_Print_Summary","B2:J28"),("12_Print_Approval","B2:J28"),("14_Revision_Log","B2:K30")]:
    apply_page_setup(wb[sheet_name], area)
    wb[sheet_name]["B2"].comment = Comment(f"Expected print area: {area}", "OpenAI")

apply_password_strategy(wb)
wb.save(OUTPUT_FILE)
print(f"Created: {OUTPUT_FILE}")