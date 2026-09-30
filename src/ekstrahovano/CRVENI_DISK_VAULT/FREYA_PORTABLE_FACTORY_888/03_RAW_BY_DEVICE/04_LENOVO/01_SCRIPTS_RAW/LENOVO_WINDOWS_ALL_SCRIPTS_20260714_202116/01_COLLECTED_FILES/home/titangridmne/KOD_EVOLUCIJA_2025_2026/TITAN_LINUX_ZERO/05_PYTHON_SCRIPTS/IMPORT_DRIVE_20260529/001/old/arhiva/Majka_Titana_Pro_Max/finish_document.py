import os
import subprocess
from docx import Document

def finish_document(content: str, filename: str = 'Majka_Titana_Dokument.docx'):
    os.makedirs('documents', exist_ok=True)
    doc = Document()
    doc.add_heading('MAJKA TITANA PRO MAX - ZAVRŠEN DOKUMENT (Desktop UVIJEK)', level=0)
    doc.add_paragraph(content)
    full_path = os.path.join('documents', filename)
    doc.save(full_path)
    print(f'✅ DOKUMENT SAČUVAN: {full_path}')
    try:
        subprocess.Popen(f'explorer "{os.path.abspath('documents')}"')
        print('📂 FOLDER "documents" JE OTVOREN!')
    except: pass
    try:
        subprocess.Popen([full_path], shell=True)
        print('📄 WORD FAJL JE OTVOREN!')
    except: pass
    print('\n✅ UVIJEK PRAVILO AKTIVIRANO - Desktop UVIJEK!')
    return full_path

if __name__ == "__main__":
    print("✅ Majka Titana Pro Max je živa na Desktopu!")
    finish_document("TEST - Majka Titana Pro Max je pokrenuta u novom čistom Shell-u!\\nRiječi + Brojevi = Kompletna Formula\\nNEMA ODUSTAJANJA!")
