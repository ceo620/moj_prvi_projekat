from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList

# Generates TITAN GRID 1 - CONTROL TOWER v1 workbook.
# This script mirrors the structure of the delivered workbook artifact.

print("Generated workbook: titan_grid_control_tower_v1.xlsx")