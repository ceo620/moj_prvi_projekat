import pandas as pd
from datetime import datetime
import os

folder = r'C:\Users\Lenovo\Desktop\CTITAN_CENTRAL_BRAINRaw_Data\00_CENTRALNI_MOZAK_MAJKA_TITANA_v24'
os.makedirs(folder, exist_ok=True)

df = pd.DataFrame([{
    'Status': 'TEST - Majka Titana radi',
    'Datum': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'Poruka': 'Folder i Excel su uspješno kreirani'
}])

df.to_excel(os.path.join(folder, 'MAJKA_TITANA_v24.xlsx'), index=False)
print('✅ Test Excel kreiran!')
os.startfile(os.path.join(folder, 'MAJKA_TITANA_v24.xlsx'))
