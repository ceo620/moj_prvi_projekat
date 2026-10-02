#!/usr/bin/env python3
"""Read the five worksheets omitted from 012's output. Standard library only.

No file writes, extraction to disk, project execution, or network access.
Saved cell values and formulas are evidence, not recalculated results.
"""
import hashlib
import io
import json
import os
import posixpath
import signal
import stat
import zipfile
import xml.etree.ElementTree as ET

BATCH = 'IPHONE_R8_013_READ_RECONCILIATION_TAIL_888'
TARGET = ('/root/FREYA_RECOVERY_009_888_ugk9zsdm/RECOVERED/root/'
          'DOCTRINES_ONLY_20260713_182636/'
          '281_TITAN_vE1_VOL08_CAPEX_RECONCILIATION_FORENSIC_SSOT.xlsx')
EXPECTED_SHA = 'e54f56b936a84a8efa4eadb96e8a6107982fa88aa7dbfabe620f25c028da00e9'
EXPECTED_BYTES = 62421
WANTED = ('04_PHASE_102_MAPPING', '05_18_2M_SCENARIO',
          '06_43_5M_SCENARIO', '07_MISSING_EVIDENCE',
          '08_RECONCILIATION_ACTIONS')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
MAX_FILE = 65536
MAX_XML = 4 * 1024 * 1024
MAX_OUTPUT = 60000
READ = XML = 0


def emit(event, **data):
    print(json.dumps(dict(event=event, **data), ensure_ascii=True), flush=True)


def timeout(*unused):
    raise TimeoutError('TIME_LIMIT')


def read_source():
    global READ
    if os.path.realpath(TARGET) != TARGET:
        raise ValueError('LINK_PATH')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(TARGET, flags), 'rb') as f:
        before = os.fstat(f.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size != EXPECTED_BYTES:
            raise ValueError('SOURCE_TYPE_OR_SIZE_CHANGED')
        raw = f.read(MAX_FILE + 1)
        READ = len(raw)
        after = os.fstat(f.fileno())
    fields = ('st_size', 'st_mtime_ns', 'st_ctime_ns')
    if any(getattr(before, k) != getattr(after, k) for k in fields):
        raise ValueError('CHANGED_DURING_READ')
    if len(raw) != EXPECTED_BYTES or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError('SOURCE_SHA256_OR_SIZE_CHANGED')
    return raw


def read_xml(z, name):
    global XML
    info = z.getinfo(name)
    if info.file_size > 1024 * 1024 or XML + info.file_size > MAX_XML:
        raise ValueError('XML_READ_LIMIT')
    with z.open(info) as f:
        raw = f.read(info.file_size + 1)
    XML += len(raw)
    if len(raw) != info.file_size:
        raise ValueError('XML_SIZE_CHANGED')
    if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:
        raise ValueError('XML_DECLARATION_NOT_SUPPORTED')
    return ET.fromstring(raw)


def collect_rows(raw):
    records = []
    total_rows = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) > 512 or len(names) != len(set(names)):
            raise ValueError('ZIP_MEMBER_COUNT_OR_DUPLICATES')
        book = read_xml(z, 'xl/workbook.xml')
        sheets = book.find('m:sheets', NS)
        if sheets is None or len(sheets) > 32:
            raise ValueError('SHEET_COUNT')
        by_name = {s.attrib['name']: s for s in sheets}
        if len(by_name) != len(sheets):
            raise ValueError('DUPLICATE_SHEET_NAME')
        missing = [name for name in WANTED if name not in by_name]
        if missing:
            raise ValueError('MISSING_SHEETS: ' + ', '.join(missing))
        relationships = read_xml(z, 'xl/_rels/workbook.xml.rels')
        rels = {r.attrib['Id']: r.attrib for r in relationships}
        if len(rels) != len(relationships):
            raise ValueError('DUPLICATE_RELATIONSHIP_ID')
        shared = []
        if 'xl/sharedStrings.xml' in names:
            shared = [''.join(t.text or '' for t in s.findall('.//m:t', NS))
                      for s in read_xml(z, 'xl/sharedStrings.xml').findall('m:si', NS)]
        for name in WANTED:
            rel = rels[by_name[name].attrib[RID]]
            if rel.get('TargetMode', 'Internal') != 'Internal':
                raise ValueError('EXTERNAL_SHEET')
            if not rel.get('Type', '').endswith('/worksheet'):
                raise ValueError('NOT_A_WORKSHEET')
            target = rel['Target']
            path = posixpath.normpath(target.lstrip('/') if target.startswith('/')
                                      else 'xl/' + target)
            if not path.startswith('xl/') or '\\' in path or '..' in path.split('/'):
                raise ValueError('SHEET_MEMBER_PATH')
            tree = read_xml(z, path)
            rows = tree.findall('m:sheetData/m:row', NS)
            if len(rows) > 100:
                raise ValueError('SHEET_ROW_LIMIT')
            nonempty = 0
            for row in rows:
                cells = []
                raw_cells = row.findall('m:c', NS)
                if len(raw_cells) > 64:
                    raise ValueError('ROW_CELL_LIMIT')
                for c in raw_cells:
                    v = c.find('m:v', NS)
                    f = c.find('m:f', NS)
                    kind = c.attrib.get('t', 'n')
                    value = v.text if v is not None else None
                    if kind == 's':
                        index = int(value)
                        if index < 0 or index >= len(shared):
                            raise ValueError('SHARED_STRING_INDEX')
                        value = shared[index]
                    elif kind == 'inlineStr':
                        value = ''.join(t.text or '' for t in c.findall('m:is//m:t', NS))
                    if value is None and f is None:
                        continue
                    cell = {'cell': c.attrib['r'], 'type': kind, 'saved_value': value}
                    if f is not None:
                        cell['formula'] = f.text
                        cell['formula_attributes'] = dict(f.attrib)
                    cells.append(cell)
                if cells:
                    nonempty += 1
                    records.append(dict(event='WORKBOOK_ROW', sheet=name,
                                        row=row.attrib.get('r'), cells=cells))
            total_rows += nonempty
            records.append(dict(event='SHEET_SCOPE', sheet=name,
                                nonempty_rows=nonempty, emitted_rows=nonempty,
                                all_cell_content_exported=True, recalculated=False))
    size = sum(len(json.dumps(r, ensure_ascii=True)) + 1 for r in records)
    if size > MAX_OUTPUT:
        raise ValueError('OUTPUT_LIMIT_NO_CELL_CONTENT_EMITTED')
    return records, total_rows, size


def main():
    emit('HEADER', batch=BATCH, mode='READ_ONLY', seconds=30,
         requested_sheets=list(WANTED), max_file_bytes=MAX_FILE,
         max_xml_bytes=MAX_XML, max_cell_output_characters=MAX_OUTPUT,
         scope='SAVED_CELL_VALUES_AND_FORMULAS_IN_FIVE_SHEETS',
         project_execution=False, network_calls=0, writes=0)
    raw = read_source()
    emit('SOURCE', path=TARGET, bytes=len(raw), sha256=EXPECTED_SHA,
         matches_012=True, authority='RECOVERED_CANDIDATE_NOT_ESTABLISHED')
    records, count, output_size = collect_rows(raw)
    for record in records:
        print(json.dumps(record, ensure_ascii=True), flush=True)
    emit('FINAL', result='FIVE_SHEET_CELL_READ_COMPLETE_REQUIRES_REVIEW',
         requested_sheets=5, sheets_read=5, nonempty_rows=count,
         selected_sheet_cell_content_complete=True, whole_workbook_exported=False,
         file_bytes_read=READ, xml_bytes_read=XML,
         cell_output_characters=output_size, recalculated=False,
         approval='NOT_ESTABLISHED', project_starts=0, writes=0,
         network_calls=0, next='VRATI_CIJELI_IZLAZ')


if __name__ == '__main__':
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(30)
    try:
        main()
    except Exception as exc:
        emit('FINAL', result='HOLD_INCOMPLETE_READ', reason=type(exc).__name__,
             detail=str(exc)[:200], file_bytes_read=READ, xml_bytes_read=XML,
             writes=0, network_calls=0, next='VRATI_CIJELI_IZLAZ')
    finally:
        signal.alarm(0)
