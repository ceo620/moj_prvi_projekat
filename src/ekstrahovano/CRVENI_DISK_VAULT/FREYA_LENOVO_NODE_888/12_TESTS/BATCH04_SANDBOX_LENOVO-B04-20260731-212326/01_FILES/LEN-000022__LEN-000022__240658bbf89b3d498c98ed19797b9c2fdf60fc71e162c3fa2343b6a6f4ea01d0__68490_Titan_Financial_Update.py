import os; from docx import Document
D = 'C:/TITAN_KONACNO'

doc = Document()
doc.add_heading('11_Key_Assumptions - UPDATED CHANGE ORDERS', 0)
doc.add_paragraph("PROJEKAT TITAN GRID - FINANSIJSKE IMPLIKACIJE IZ DASHBOARD-A")
doc.add_paragraph("\nUTICAJ NA BUDŽET I ROKOVE:\n")
doc.add_paragraph("- Građevinski radovi (Beton Mont): Povećan CAPEX zbog stabilizacije tla.")
doc.add_paragraph("- Elektro/Oprema (ABB/Elkom): Investicija u digitalizaciju (SCADA i kontroleri).")
doc.add_paragraph("- ROKOVI: Zabilježeno kašnjenje u građevinskoj fazi (ID 10).")
doc.add_paragraph("\nSve stavke su preuzete direktno iz sirove materije: Change Order Dashboard.")
doc.save(os.path.join(D, "11_Key_Assumptions.docx"))
print("🚀 DOKUMENT 11 JE AŽURIRAN SA CIFRAMA IZ DASHBOARDA!")
