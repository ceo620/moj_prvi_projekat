#!/usr/bin/env python3
"""Copy only the nine reviewed files, preserving originals and verifying hashes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys

ROOT = Path('/root/FREYA_RAD_888')
REC = Path('/root/FREYA_RECOVERY_009_888_ugk9zsdm/RECOVERED/root')
OBJ = Path('/root/FREYA_DEEP_016_888/OBJECTS')
DEEP = REC/'faza0_doktrine/root/Documents/TITAN_Grid_Financial_Model_CSV_Exports 2/IPHONE_MCR_AGGRESSIVE_COPY_20260707_204647/08_UNPACKED_RAW/6_IPHONE_TITAN_EXPORT_PACKET.tar.gz/IPHONE_TITAN_EXPORT_PACKET'
NODE = REC/'FREYA_IPHONE_ISH_NODE_888'
ITEMS = [
 (OBJ/'e885ba6e3c7c6b1b56aa7d5afe37d1eae7e3cce182c0ae159e27e8ae32805801.py', '01_KOD/AUTOMATE_ALL_DOCUMENTS.py', 'e885ba6e3c7c6b1b56aa7d5afe37d1eae7e3cce182c0ae159e27e8ae32805801', 'UPDATES_EXISTING_FILES; NOT_DOCUMENT_FACTORY'),
 (OBJ/'180882bc799ed5cfe4aacb6eed8caea1cc458cdacbd98c4de25e071a4effd2a3.py', '01_KOD/PATCHED_32_DATA_ROOM_BUILDER.py', '180882bc799ed5cfe4aacb6eed8caea1cc458cdacbd98c4de25e071a4effd2a3', 'DRY_RUN_COMMENT_ONLY; WRITES_WHEN_EXECUTED'),
 (OBJ/'6f6f336c828ce6c63d01305ed2c3e090edc666e3b7a024a088eea70c6c8bec2c.py', '02_ADAPTERI/ADAPTER_PATCHED_32.py', '6f6f336c828ce6c63d01305ed2c3e090edc666e3b7a024a088eea70c6c8bec2c', 'PRINT_ONLY; ORIGINAL_EMBEDDED_AS_TEXT'),
 (OBJ/'50cb6d96d7fb0615a6a6eb243bc5c13f16b45cf18e83f3778f712cd216ced08a.py', '02_ADAPTERI/TITAN_ADAPTER_42.py', '50cb6d96d7fb0615a6a6eb243bc5c13f16b45cf18e83f3778f712cd216ced08a', 'PRINT_ONLY; ORIGINAL_EMBEDDED_AS_TEXT'),
 (DEEP/'_root_Documents_569_generate_SIGNALNI_MEMORANDUM_TITAN1.py', '01_KOD/generate_SIGNALNI_MEMORANDUM_TITAN1.py', '97a18cecc6af347637429d2765731ee758a2b0597568c702430ed27b504507ac', 'ONE_DOCUMENT_GENERATOR; REGISTER_V4_SCHEMA_MISMATCH; FIXED_DATE'),
 (REC/'faza0_skripte/FREYA_SSOT/24_TITAN_WORKING_ADAPTERS/TITAN_ADAPTER_35__root_Documents_569_generate_SIGNALNI_MEMORANDUM_TITAN1.py', '02_ADAPTERI/TITAN_ADAPTER_35.py', '534eb1e0396617b6f05b022eb8e0b040a3f51f02d9c3b1950bef366bb7be944f', 'PRINT_ONLY; ORIGINAL_EMBEDDED_AS_TEXT'),
 (Path('/root/FREYA_SEGMENTS_014_d_20s9r2/PAYLOAD/DOCTRINE_PROJECT/JSON/02367_FREYA_SSOT__08_EXTRACTED__3_IPHONE_TITAN_EXPORT_PACKET.tar.gz__IPHONE_TITAN_EXPORT_PACKET___root_Documents_FINAL_SEND_PACKAGE_TITAN1_2026-05-10_MASTER_TOKEN_REGISTER_v4.0.json'), '03_REGISTAR/MASTER_TOKEN_REGISTER_v4.0.json', '0e48b67c613112084747ba9edcb58faa383d78653a8ee020ff49eb6157a35c5e', 'HISTORICAL_TITAN1_CTOS_V4; CURRENT_APPROVAL_NOT_VERIFIED'),
 (NODE/'07_RELAY/IPHONE_TO_MSI_20260812T131026Z/FREYA_IPHONE_TO_MSI_20260812T131026Z.tar.gz', '04_ARHIVE/MSI_KONTROLNI_HANDOFF.tar.gz', '7ff372e025691c01325e5c18e3e4be7a8502c747d30c97881e3bf23f37b74abb', 'CONTROL_ONLY; RUNTIME_INCLUDED_NO; ORIGINALS_INCLUDED_NO'),
 (NODE/'12_QUARANTINE/IPHONE_PRO_BATCH_01_20260821T173048Z/EXACT_DUPLICATES/18_HANDOFF/IPHONE_TO_ANDROID_TITAN_DATAROOM_20260819T124950Z/MILOS_HANDOFF_888/01_PAYLOAD/IPHONE_TO_ANDROID_TITAN_DATAROOM_20260819T124950Z.tar.gz', '04_ARHIVE/IPHONE_TO_ANDROID_TITAN_DATAROOM.tar.gz', '37fe9babf6bf39c4553da9bd4d42d8ff7110f1c9438fe0f42e880390865e7070', 'DOCUMENT_PACKAGE; NESTED_ZIP_NOT_INSPECTED; NOT_VERIFIED_FACTORY'),
]

def directory(p):
    for q in (p, *p.parents):
        if not stat.S_ISDIR(q.lstat().st_mode):
            raise ValueError('FOLDER_ILI_LINK_NIJE_DOZVOLJEN: ' + str(q))

def mkdir(p):
    if not os.path.lexists(p):
        directory(p.parent)
        p.mkdir(mode=0o700)
    directory(p)

def same(p, data):
    if not os.path.lexists(p):
        return False
    directory(p.parent)
    if not stat.S_ISREG(p.lstat().st_mode) or p.read_bytes() != data:
        raise ValueError('POSTOJECI_FAJL_SE_RAZLIKUJE: ' + str(p))
    return True

def write_new(p, data):
    if same(p, data):
        return
    directory(p.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(str(p), flags, 0o600), 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def collect(root=ROOT, items=ITEMS):
    directory(root)
    directory(root/'ULAZ')
    dest = root/'PRONADJENI_DIJELOVI_888'
    files = {}
    manifest = []
    for source, name, expected, meaning in items:
        directory(source.parent)
        st = source.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_size > 8*1024*1024:
            raise ValueError('IZVOR_NIJE_OCEKIVANI_FAJL: ' + str(source))
        content = source.read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        if actual != expected:
            raise ValueError('IZVOR_HASH_NIJE_ISTI: ' + str(source))
        files[name] = content
        manifest.append({'source':str(source), 'copy':name, 'sha256':actual, 'bytes':len(content), 'meaning':meaning, 'executed':False})
    files['MANIFEST.json'] = (json.dumps({'protocol':888,'action':'COPY_ONLY','originals_changed':False,'factory_recovered':False,'files':manifest}, ensure_ascii=False, indent=2)+'\n').encode()
    files['PROCITAJ_PRVO.txt'] = '''PRONADJENI DIJELOVI TITAN / FREYA — 888
Ovdje su kopije devet pregledanih fajlova. Originali su sacuvani.
Svaki izvor i kopija provjeravaju se prema hashu iz izlaza iSH-a.
Hash identifikuje sadrzaj; ne dokazuje da je kod funkcionalan ili odobren.

01_KOD: generator jednog memoranduma i dvije verzije alata za osvjezavanje
postojecih dokumenata. Nije pronadjena cijela data room fabrika.
Generator memoranduma nije kompatibilan sa registrom v4 bez dorade.
Kod oznacen DRY_RUN komentarom ipak pise fajlove kad se izvrsi.
02_ADAPTERI: tri omotaca koji samo ispisuju status. Originalni kod je tekst.
03_REGISTAR: istorijski TITAN1_CTOS v4.0 od 10.05.2026, sa iznosom 18,2M.
Naziv ACTIVE_CANONICAL nije nova potvrda vazeceg odobrenja.
04_ARHIVE: MSI kontrolni paket bez runtime-a i Android data room dokumenti.
Arhive nisu raspakovane. Ugnijezdeni ZIP tek treba pregledati.

Nista od pronadjenog koda nije pokrenuto, aktivirano ili povezano sa SSOT.
Naredni posao: procitati ugnijezdenu arhivu i pronaci izvrsni MSI sistem,
njegove baze, konfiguracije, sablone i zavisnosti.
'''.encode()
    # Validate all existing destinations before any write. Repeats reuse equal bytes.
    if os.path.lexists(dest):
        directory(dest)
        for folder in {str(Path(name).parent) for name in files} - {'.'}:
            if os.path.lexists(dest/folder):
                directory(dest/folder)
        for name, data in files.items():
            same(dest/name, data)
    if shutil.disk_usage(root).free < sum(map(len, files.values())) + 2*1024*1024:
        raise ValueError('NEMA_DOVOLJNO_PROSTORA')
    mkdir(dest)
    for folder in sorted({str(Path(name).parent) for name in files} - {'.'}):
        mkdir(dest/folder)
    for name, data in files.items():
        write_new(dest/name, data)
    for name, data in files.items():
        if not same(dest/name, data):
            raise ValueError('KOPIJA_NIJE_POTVRDJENA')
    print('RESULT=IZDVOJENO_I_HASH_PROVJERENO')
    print('IZVORNIH_FAJLOVA=' + str(len(items)))
    print('FOLDER=' + str(dest))
    print('ORIGINALI=SACUVANI | POKRETANJE_KODA=NE')
    print('FABRIKA=JOS_NIJE_CIJELA_PRONADJENA')

if __name__ == '__main__':
    if sys.argv[1:] != ['--izdvoji-888']:
        print('HOLD=OCEKIVANO_--izdvoji-888')
        sys.exit(2)
    try:
        collect()
    except Exception as e:
        print('HOLD=' + str(e))
        sys.exit(2)
