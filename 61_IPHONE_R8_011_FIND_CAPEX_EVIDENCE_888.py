#!/usr/bin/env python3
"""Read existing inventory only; locate CAPEX source candidates, never activate them."""
import csv
import hashlib
import io
import json
import os
import re
import signal
import stat
import unicodedata

INDEX = '/root/FREYA_RAD_888/DIJAMANTI_POPIS.csv'
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 20000
MAX_OUTPUT = 60


def emit(event, **data):
    print(json.dumps(dict(event=event, **data), ensure_ascii=True), flush=True)


def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold())
                   if not unicodedata.combining(c))


def timeout(*unused):
    raise TimeoutError('TIME_LIMIT')


def search(raw):
    text = raw.decode('utf-8-sig', errors='strict')
    try:
        dialect = csv.Sniffer().sniff(text[:16384], delimiters=',;\t|')
    except csv.Error:
        raise ValueError('CSV_DELIMITER_NOT_ESTABLISHED')
    reader = csv.reader(io.StringIO(text), dialect)
    header = next(reader, [])
    if not header or len(header) > 80 or any(len(x) > 160 for x in header):
        raise ValueError('CSV_HEADER_LIMIT')
    cols = [i for i, x in enumerate(header)
            if re.search(r'path|putanj|filename|file_name|naziv|ime_fajla|member|entry_name', norm(x))
            or norm(x).strip() in ('file', 'name', 'fajl', 'source', 'destination', 'izvor')]
    emit('INVENTORY_SCHEMA', columns=header,
         searched_columns=[header[i] for i in cols])
    if not cols:
        raise ValueError('PATH_COLUMNS_NOT_IDENTIFIED')
    # Match filenames/paths only, never unrelated CSV payload columns.
    terms = [('elaborat', 100), ('18200000', 100), ('18.2', 90), ('18,2', 90),
             ('crosswalk', 85), ('odluk', 80), ('odobren', 80),
             ('approval', 70), ('signoff', 70), ('sign_off', 70),
             ('troskov', 75), ('predracun', 75), ('ponud', 65),
             ('boq', 65), ('razrad', 70), ('capex', 50),
             ('budget', 45), ('budzet', 45)]
    reviewed = ('capex_full_v2_bank_model_harmonized_v20',
                'titan_grid_fully_linked_project_finance_model_v3_4_fixed',
                'titan_lender_v6_2_ispravljeno_888',
                'titan_grid_v6_2_live_lender_linkage_pack',
                'titan_finance_master_v6_1_ispravljeno_888',
                'titan_central_brain_finance_master_v6_1',
                'uni_mak_capex_ispravljeno_888',
                'uni-mak_capex_log-001_a4_ready',
                'aneks_1_revizija_capex_titan1_professional_final_2026-05-10',
                'signalni_memorandum_titan1_2026-05-10',
                'master_token_register_v4.0')
    found = []; seen = set(); rows = 0; skipped = 0
    for row in reader:
        if not row or not any(row):
            continue
        rows += 1
        if rows > MAX_ROWS:
            raise ValueError('ROW_LIMIT')
        if len(row) != len(header):
            raise ValueError('CSV_ROW_WIDTH_AT_' + str(rows))
        paths = tuple(row[i] for i in cols if row[i])
        if not paths:
            continue
        value = norm(' '.join(paths))
        if any(old in value for old in reviewed):
            skipped += 1
            continue
        reasons = [(term, weight) for term, weight in terms if term in value]
        if not reasons or paths in seen:
            continue
        seen.add(paths)
        found.append((max(w for t, w in reasons), paths,
                      [t for t, w in reasons],
                      {header[i]: row[i] for i in cols if row[i]}))
    found.sort(key=lambda x: (-x[0], x[1]))
    for number, (_, paths, terms_found, fields) in enumerate(found[:MAX_OUTPUT], 1):
        emit('SOURCE_CANDIDATE', number=number, locations=fields,
             matched_terms=terms_found, authority='NOT_ESTABLISHED',
             current_file_presence='NOT_CHECKED')
    emit('FINAL', result='EXISTING_INVENTORY_SEARCH_COMPLETE',
         inventory_rows_read=rows, inventory_enumeration_complete=True,
         matching_unique_records=len(found), reported=min(len(found), MAX_OUTPUT),
         all_matches_reported=len(found) <= MAX_OUTPUT,
         reviewed_filename_rows_skipped=skipped,
         search_scope='SELECTED_INVENTORY_PATH_COLUMNS_ONLY',
         filesystem_search_complete=False, inventory_freshness='NOT_ESTABLISHED',
         candidate_contents_read=False, source_writes=0, network_calls=0,
         next='VRATI_CIJELI_IZLAZ')


def main():
    emit('HEADER', batch='IPHONE_R8_011_FIND_CAPEX_EVIDENCE_888',
         mode='READ_ONLY', index=INDEX, max_seconds=30,
         max_bytes=MAX_BYTES, max_output=MAX_OUTPUT,
         project_execution=False, network_calls=0)
    if os.path.realpath(INDEX) != INDEX:
        raise ValueError('LINK_PATH')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(INDEX, flags), 'rb') as f:
        before = os.fstat(f.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise ValueError('FILE_TYPE_OR_SIZE')
        raw = f.read(MAX_BYTES + 1)
        after = os.fstat(f.fileno())
    if len(raw) > MAX_BYTES or len(raw) != before.st_size:
        raise ValueError('READ_SIZE')
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('INDEX_CHANGED_DURING_READ')
    emit('INVENTORY_READ', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
         authority='SEARCH_INDEX_ONLY')
    search(raw)


if __name__ == '__main__':
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(30)
    try:
        main()
    except Exception as exc:
        emit('FINAL', result='HOLD_READ_NOT_COMPLETE',
             reason=type(exc).__name__, detail=str(exc)[:180],
             source_writes=0, network_calls=0, next='VRATI_CIJELI_IZLAZ')
    finally:
        signal.alarm(0)
