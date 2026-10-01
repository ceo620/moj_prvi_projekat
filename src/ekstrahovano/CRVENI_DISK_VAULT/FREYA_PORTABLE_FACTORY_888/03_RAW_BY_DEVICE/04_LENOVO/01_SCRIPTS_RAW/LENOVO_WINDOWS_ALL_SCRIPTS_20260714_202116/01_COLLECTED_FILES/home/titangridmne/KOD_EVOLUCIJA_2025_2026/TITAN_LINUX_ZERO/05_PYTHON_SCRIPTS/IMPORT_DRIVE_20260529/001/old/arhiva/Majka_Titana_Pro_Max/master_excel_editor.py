import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import os

# ================================================
# MAJKA TITANA PRO MAX - SAVRŠENI MASTER EXCEL
# ================================================

def create_master_excel():
    file_path = Path('ARS_Metal_Industries_Master_Excel.xlsx')
    
    # Sheet 1: INVENTORY & ITEMS (iz CSV header-a koji si dao)
    inventory_data = {
        'Item_ID': [''],
        'Açıklama (Description)': [''],
        'Kategori (Category)': [''],
        'Yıllık Talep (Annual Demand)': [0],
        'Birim Maliyet (TRY) (Unit Cost TRY)': [0.0],
        'Mevcut Stok (Current Stock)': [0],
        'Teslim Süresi (gün) (Lead Time days)': [0],
        'Daily Demand': [0.0],
        'Stock Value (TRY)': [0.0]
    }
    df_inventory = pd.DataFrame(inventory_data)
    
    # Sheet 2: OPEX SCENARIOS (Low / Base / High)
    opex_data = {
        'Scenario': ['Low', 'Base', 'High'],
        'Cijena Čelika (TRY/t)': [850, 950, 1100],
        'Produktivnost Rada (kom/h)': [12, 15, 18],
        'Energetska Efikasnost (kWh/t)': [420, 380, 340],
        'Inflacija (%)': [3.5, 5.0, 7.0],
        'Bruto Plata Prosjek (€)': [950, 1100, 1300],
        'Rast Plata (%)': [4, 6, 8]
    }
    df_opex = pd.DataFrame(opex_data)
    
    # Sheet 3: FINANCIAL SUMMARY 15Y (placeholder - ti ćeš popuniti)
    financial_summary = {
        'Godina': list(range(2026, 2041)),
        'Revenue (mil €)': [0]*15,
        'OPEX (mil €)': [0]*15,
        'EBITDA (mil €)': [0]*15,
        'CAPEX (mil €)': [0]*15,
        'Free Cash Flow (mil €)': [0]*15,
        'NPV (mil €)': [0]*15
    }
    df_fin = pd.DataFrame(financial_summary)
    
    # Sheet 4: RISK MATRIX
    risk_data = {
        'Risk': ['HDG segment tank line', 'Automation package', 'Čelik cijena', 'Radna snaga', 'Regulatorni'],
        'Delta (€)': [1440000, 180000, 0, 0, 0],
        'New Total (€)': [34874115, 33614115, 0, 0, 0],
        'Comment': ['+30%', '+15%', '', '', '']
    }
    df_risk = pd.DataFrame(risk_data)
    
    # Sheet 5: MASTER INDEX (70 dokumenata placeholder)
    master_index = {
        'Document_ID': ['ARS_19', 'ARS_21', 'ARS_23', 'PB-DSGN-1.1.9-001', 'FIN-2.7', '...'],
        'Naziv': ['Global Competitor Database', 'Competitive Landscape Map', 'Cost Benchmark', 'Design Proposal', 'Working Capital Model', ''],
        'PILLAR': ['Market', 'Market', 'Financial', 'Technical', 'Financial', ''],
        'Status': ['Draft', 'Draft', 'Draft', 'For Approval', 'Draft', '']
    }
    df_index = pd.DataFrame(master_index)
    
    # Kreiraj Excel sa više sheet-ova
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df_inventory.to_excel(writer, sheet_name='INVENTORY', index=False)
        df_opex.to_excel(writer, sheet_name='OPEX_SCENARIOS', index=False)
        df_fin.to_excel(writer, sheet_name='FINANCIAL_15Y', index=False)
        df_risk.to_excel(writer, sheet_name='RISK_MATRIX', index=False)
        df_index.to_excel(writer, sheet_name='MASTER_INDEX', index=False)
    
    # Formatiranje (ljepši izgled)
    wb = load_workbook(file_path)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        # Bold header
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        # Auto width
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(file_path)
    print(f'✅ SAVRŠENI MASTER EXCEL KREIRAN: {file_path}')
    print('📊 Sheet-ovi: INVENTORY, OPEX_SCENARIOS, FINANCIAL_15Y, RISK_MATRIX, MASTER_INDEX')
    
    # Otvori Excel automatski
    os.startfile(file_path)
    return file_path

if __name__ == "__main__":
    create_master_excel()
    print('\n✅ Majka Titana Pro Max je spremna za uređivanje savršenog Excela!')
    print('   Sada možeš da popunjavaš podatke i mi ćemo ga dalje poboljšavati.')
