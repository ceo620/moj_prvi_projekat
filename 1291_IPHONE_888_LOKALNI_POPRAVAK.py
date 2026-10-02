#!/usr/bin/env python3
"""PROTOCOL 888: repair the reviewed existing XLSX validator and retest local modules.
No API, network, credential, install, canonical switch or background-service action.
Only new output directories and copies are written. Existing eight input copies are reused.
The earlier zero-formula observation is superseded, not erased.
Run --popravi-888 once to prepare the corrected reusable modules and execute tests.
No argument performs no mutation. Original workbooks and audit sheets are not edited.
"""
import datetime
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

SOURCE = Path('/root/FREYA_RECOVERY_009_888_ugk9zsdm/RECOVERED/root/FREYA_IPHONE_ISH_NODE_888')
GATEWAY = Path('/tmp/ISH_EXPORT_888.w75MRJ')
ARCHIVE_SHA = 'f800186885861b62ce5758a5891b73adeac61af68a412ff920429fb62f94e06b'
MODULES = {
    'document_processor.py': (
        '15_RUNTIME/FOREGROUND_BUSINESS_RELEASES/V1R3_20260805T230000Z_SSOT_EVIDENCE_CANDIDATE/document_processor.py',
        '8236c31e63747752248df5c70c13e7d3786dd53336387bb115a63fef5cc8f64d'),
    'financial_validator_v2_888.py': (
        '16_V2_DEVELOPMENT/ACTIVATION_CANDIDATES/V2P2_AC_20260806T182404Z_5320/release/agent_intelligence_888/financial_validator_v2_888.py',
        '97a77c63383646e81e56e2b5712714778dee6e4e9235b0d71e92cd1431a67db1'),
}
REAL_NAMES = (
    'TITAN_Central_Brain_Finance_Master_v6_1.xlsx',
    'Titan_Grid_v6_2_Live_Lender_Linkage_Pack.xlsx',
    'UNI-MAK_CAPEX_LOG-001_A4_READY.xlsx',
    'ORG-005_TITAN_Grid_Teaser_v4.xlsx',
    'ORG-016_TITAN_Grid_Project_Charter_v4.xlsx',
    'ANEKS_1_REVIZIJA_CAPEX_TITAN1_PROFESSIONAL_FINAL_2026-05-10.docx',
    'Titan_Grid_Collateral_Overview_v2_Bank_Ready.docx',
    'Debt.csv',
)
DATA_SUFFIXES = {'.xlsx', '.xls', '.csv', '.docx', '.doc', '.pdf', '.txt', '.md'}
MAX_FILE = 24 * 1024 * 1024
MAX_TOTAL = 96 * 1024 * 1024
TIMEOUT = 40


class Hold(Exception):
    pass


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    path = Path(path)
    if isinstance(data, str):
        data = data.encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(data)


def write_json(path, obj):
    write_new(path, json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def stable_read(path, limit=MAX_FILE):
    """Read one regular file without following any symlink in its path."""
    path = Path(os.path.abspath(str(path)))
    for component in (path,) + tuple(path.parents):
        if component.is_symlink():
            raise Hold('SYMLINK_NOT_USED: ' + str(component))
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise Hold('NOT_REGULAR_OR_TOO_LARGE: ' + str(path))
    with path.open('rb') as f:
        opened = os.fstat(f.fileno())
        data = f.read(limit + 1)
        after = os.fstat(f.fileno())
    key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if (len(data) > limit or len(data) != before.st_size or
            key(before) != key(opened) or key(opened) != key(after) or
            key(after) != key(path.stat())):
        raise Hold('SOURCE_CHANGED_DURING_READ: ' + str(path))
    return data


def run_module(session, name, args, log):
    module = session / 'CODE' / name
    if digest(stable_read(module, 524288)) != MODULES[name][1]:
        raise Hold('EXECUTABLE_HASH_MISMATCH: ' + name)
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(session), 'LC_ALL': 'C',
           'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run(
        [sys.executable, '-I', '-S', '-B', str(module)] + [str(a) for a in args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=TIMEOUT, cwd=str(session), env=env)
    text = (result.stdout + result.stderr).decode('utf-8', 'replace')
    write_new(log, text)
    return result.returncode, text


def fields(text):
    return dict(line.split('=', 1) for line in text.splitlines() if '=' in line)


def check_xlsx_bounds(path):
    # The existing keyword checker reads all XML into memory; bound that input.
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        if len(entries) > 2500:
            raise Hold('XLSX_TOO_MANY_ENTRIES')
        if len({i.filename for i in entries}) != len(entries):
            raise Hold('XLSX_DUPLICATE_ZIP_NAMES')
        xmls = [i for i in entries if i.filename.endswith('.xml')]
        if sum(i.file_size for i in xmls) > 16 * 1024 * 1024:
            raise Hold('XLSX_XML_TOTAL_LIMIT')
        if any(i.file_size > 8 * 1024 * 1024 or i.flag_bits & 1 for i in xmls):
            raise Hold('XLSX_XML_ENTRY_LIMIT_OR_ENCRYPTION')


def process_file(session, original, destination, kind):
    started = utc()
    if original.suffix.lower() not in DATA_SUFFIXES:
        raise Hold('UNSUPPORTED_DATA_EXTENSION')
    data = stable_read(original)
    source_sha = digest(data)
    # Only task-owned copies are passed to the reviewed processors.
    copy_path = destination / 'INPUT' / ('source' + original.suffix.lower())
    write_new(copy_path, data)
    if digest(stable_read(copy_path)) != source_sha:
        raise Hold('INPUT_COPY_HASH_MISMATCH')
    code, text = run_module(session, 'document_processor.py',
                            [copy_path, destination / 'PROCESSOR'], destination / 'PROCESSOR.log')
    if code != 0:
        raise Hold('DOCUMENT_PROCESSOR_EXIT_' + str(code))
    receipt = json.loads(stable_read(destination / 'PROCESSOR' / 'RECEIPT.json', 100000))
    classifications = {'.pdf': 'DOCUMENT', '.doc': 'DOCUMENT', '.docx': 'DOCUMENT',
                       '.xls': 'FINANCIAL', '.xlsx': 'FINANCIAL', '.csv': 'FINANCIAL',
                       '.txt': 'TEXT', '.md': 'TEXT'}
    if (receipt.get('sha256') != source_sha or receipt.get('bytes') != len(data) or
            receipt.get('source') != str(copy_path) or receipt.get('result') != 'PASS' or
            receipt.get('classification') != classifications[original.suffix.lower()]):
        raise Hold('DOCUMENT_RECEIPT_VERIFICATION_FAILED')
    result = {
        'kind': kind, 'source': str(original), 'source_name': original.name,
        'source_sha256': source_sha, 'bytes': len(data), 'started_utc': started,
        'receipt': str((destination / 'PROCESSOR' / 'RECEIPT.json').relative_to(session)),
        'receipt_sha256': digest(stable_read(destination / 'PROCESSOR' / 'RECEIPT.json', 100000)),
        'document_processor': 'PASS_HASH_AND_CLASSIFICATION',
        'financial_content_accuracy': 'NOT_ASSESSED', 'business_approval': 'NOT_GRANTED',
        'xlsx_keyword_check': 'NOT_APPLICABLE',
    }
    if original.suffix.lower() == '.xlsx':
        try:
            check_xlsx_bounds(copy_path)
            code, text = run_module(session, 'financial_validator_v2_888.py', [copy_path],
                                    destination / 'XLSX_KEYWORDS.log')
            parsed = fields(text)
            result['xlsx_keyword_check'] = ('PASS_LIMITED_CHECK' if code == 0 and
                                           parsed.get('RESULT') == 'PASS' else 'HOLD')
            result['xlsx_exit_code'] = code
            result['xlsx_checks'] = parsed
        except (Hold, zipfile.BadZipFile, RuntimeError, subprocess.TimeoutExpired) as exc:
            result['xlsx_keyword_check'] = 'HOLD'
            result['xlsx_reason'] = type(exc).__name__ + ': ' + str(exc)
    after = digest(stable_read(original))
    if after != source_sha or digest(stable_read(copy_path)) != source_sha:
        raise Hold('SOURCE_OR_INPUT_COPY_HASH_CHANGED')
    result['source_sha256_after'] = after
    result['source_content_unchanged_observed'] = True
    result['completed_utc'] = utc()
    write_json(destination / 'LINEAGE.json', result)
    return result


def fixture_xlsx(path, formula=True):
    """Synthetic parser fixture. It does not represent a business workbook."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>')
        z.writestr('xl/worksheets/sheet1.xml', '<worksheet><sheetData><row><c><is><t>'
                   'SYNTHETIC TEST ONLY assumption EUR 2026 capex opex debt irr scenario sensitivity'
                   '</t></is></c><c>' + ('<f>1+1</f><v>2</v>' if formula else '<v>2</v>') +
                   '</c></row></sheetData></worksheet>')


def tests(session):
    base = session / 'TESTS'
    csv = base / 'FIXTURES' / 'synthetic.csv'
    write_new(csv, 'SYNTHETIC_TEST_ONLY,amount,currency\ncanary,100,EUR\n')
    first = process_file(session, csv, base / 'CSV_FIRST', 'SYNTHETIC_TEST')
    repeat = process_file(session, csv, base / 'CSV_REPEAT', 'SYNTHETIC_TEST')
    good = base / 'FIXTURES' / 'synthetic_with_formula.xlsx'
    fixture_xlsx(good)
    good_result = process_file(session, good, base / 'XLSX_GOOD', 'SYNTHETIC_TEST')
    no_formula = base / 'FIXTURES' / 'synthetic_no_formula.xlsx'
    fixture_xlsx(no_formula, False)
    negative = process_file(session, no_formula, base / 'XLSX_NO_FORMULA', 'SYNTHETIC_TEST')
    broken = base / 'FIXTURES' / 'not_a_zip.xlsx'
    write_new(broken, 'SYNTHETIC CORRUPT XLSX')
    bad_code, bad_text = run_module(session, 'financial_validator_v2_888.py', [broken],
                                    base / 'CORRUPT_XLSX.log')
    missing_code, _ = run_module(session, 'document_processor.py',
                                 [base / 'does_not_exist.csv', base / 'MISSING_OUTPUT'],
                                 base / 'MISSING_INPUT.log')
    checks = {
        'document_receipt_verified': first['document_processor'] == 'PASS_HASH_AND_CLASSIFICATION',
        'repeat_input_same_content_hash': first['source_sha256'] == repeat['source_sha256'],
        'xlsx_positive_fixture': good_result['xlsx_keyword_check'] == 'PASS_LIMITED_CHECK',
        'xlsx_no_formula_hold_despite_exit_zero': negative['xlsx_keyword_check'] == 'HOLD' and negative['xlsx_exit_code'] == 0,
        'corrupt_xlsx_rejected': bad_code != 0 and fields(bad_text).get('RESULT') == 'HOLD',
        'missing_input_rejected': missing_code != 0 and not (base / 'MISSING_OUTPUT').exists(),
    }
    write_json(base / 'TEST_RESULTS.json', checks)
    if not all(checks.values()):
        raise Hold('MODULE_TEST_FAILED')
    return checks


FIXED_VALIDATOR = b'import sys,zipfile,re,os\nimport xml.etree.ElementTree as ET\n\np=sys.argv[1]\nchecks={}\nsignals=set()\nformulas=0\n\ntry:\n    with zipfile.ZipFile(p) as z:\n        names=set(z.namelist())\n\n        checks["XLSX_STRUCTURE"] = (\n            "[Content_Types].xml" in names and\n            "xl/workbook.xml" in names\n        )\n\n        text=""\n\n        for n in names:\n            if not n.endswith(".xml"):\n                continue\n\n            raw=z.read(n)\n            x=raw.decode("utf-8","strict").lower()\n            text+=" "+x\n            if n.startswith("xl/worksheets/"):\n                if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():\n                    raise ValueError("XML_DTD_OR_ENTITY_NOT_ALLOWED")\n                root=ET.fromstring(raw)\n                allowed={"f", "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f",\n                         "{http://purl.oclc.org/ooxml/spreadsheetml/main}f"}\n                formulas += sum(node.tag in allowed for node in root.iter())\n\n        domains={\n            "ASSUMPTIONS":["assumption"],\n            "CURRENCY":["eur","usd","currency"],\n            "PERIOD":["2026","2027","2028"],\n            "CAPEX":["capex"],\n            "OPEX":["opex"],\n            "DEBT":["debt","dscr"],\n            "IRR":["irr"],\n            "SCENARIO":["scenario"],\n            "SENSITIVITY":["sensitivity"]\n        }\n\n        for k,terms in domains.items():\n            ok=any(t in text for t in terms)\n            checks[k]=ok\n            if ok:\n                signals.add(k)\n\nexcept Exception as e:\n    print("FILE="+os.path.basename(p))\n    print("RESULT=HOLD")\n    print("ERROR="+str(e))\n    raise SystemExit(1)\n\nprint("FILE="+os.path.basename(p))\nprint("FORMULAS="+str(formulas))\n\nfor k in sorted(checks):\n    print(k+"_VALIDATOR="+("PASS" if checks[k] else "HOLD"))\n\ncritical=[\n    checks.get("XLSX_STRUCTURE",False),\n    formulas>0,\n    checks.get("ASSUMPTIONS",False),\n    checks.get("CURRENCY",False),\n    checks.get("PERIOD",False)\n]\n\nprint("DOMAIN_SIGNALS="+str(len(signals)))\nprint("SOURCE_CHANGED=0")\nprint("RESULT="+("PASS" if all(critical) else "HOLD"))\n'

PREVIOUS = Path('/root/IPHONE_888_OBRADA_9dltg97z')
SUMMARY_SHA = '7c2391c246c92dbe0249442a1165bc747db1d4d6b8b4461218959c5a998edf7b'
OLD_VALIDATOR_SHA = '9b0fb67df55c8eaaa17a54621659f80970fe265e2cfc60371effce6d1c256612'
UNI_SHA = '1ecbad9e91f9263cfd09c1dae6cf419cbab7fadde856085dcfc7904f7ba958e1'


def regression_tests(session):
    checks = tests(session)
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    strict = 'http://purl.oclc.org/ooxml/spreadsheetml/main'
    for label, uri, prefix, count in [('default', ns, '', 2), ('prefixed', ns, 'x:', 2),
                                     ('strict', strict, 's:', 2), ('zero', ns, 'x:', 0)]:
        attrs = 'xmlns%s="%s"' % ((':'+prefix[:-1]) if prefix else '', uri)
        f = ('<%sf>1+1</%sf><%sf t="shared" si="0"/>' % (prefix,prefix,prefix)) if count else ''
        xml = '<%sworksheet %s><%ssheetData><%srow><%sc>%s</%sc></%srow></%ssheetData></%sworksheet>' % (
              prefix,attrs,prefix,prefix,prefix,f,prefix,prefix,prefix,prefix)
        path=session/'TESTS'/'FIXTURES'/(label+'.xlsx')
        with zipfile.ZipFile(path,'x') as z:
            z.writestr('[Content_Types].xml','<Types/>')
            z.writestr('xl/workbook.xml','<workbook/>')
            z.writestr('xl/worksheets/sheet1.xml',xml)
            z.writestr('customXml/test.xml','<root><f>NOT_A_CELL_FORMULA</f></root>')
        code,text=run_module(session,'financial_validator_v2_888.py',[path],session/'TESTS'/(label+'.log'))
        checks['formula_count_'+label] = code==0 and fields(text).get('FORMULAS')==str(count)
    path=session/'TESTS'/'FIXTURES'/'malformed.xlsx'
    with zipfile.ZipFile(path,'x') as z:
        z.writestr('[Content_Types].xml','<Types/>');z.writestr('xl/workbook.xml','<workbook/>')
        z.writestr('xl/worksheets/sheet1.xml','<worksheet><f>1+1</worksheet>')
    code,text=run_module(session,'financial_validator_v2_888.py',[path],session/'TESTS'/'malformed.log')
    checks['malformed_worksheet_rejected']=code!=0 and fields(text).get('RESULT')=='HOLD'
    write_json(session/'TESTS'/'REGRESSION_RESULTS.json',checks)
    if not all(checks.values()):raise Hold('REGRESSION_TEST_FAILED')
    return checks


def finish(session, report):
    write_json(session/'REZULTAT.json',report)
    esc=html.escape
    rows=''.join('<tr><td>'+esc(r['name'])+'</td><td>'+esc(str(r.get('old_formula_count','—')))+
        '</td><td>'+esc(str(r.get('new_formula_count','—')))+'</td><td>'+esc(r['status'])+'</td></tr>' for r in report['files'])
    page='''<!doctype html><html lang="sr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>FREYA lokalna provjera</title><style>body{font:17px system-ui;background:#f2f5f7;color:#182e3b;padding:20px}main{max-width:950px;margin:auto}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left;overflow-wrap:anywhere}p{line-height:1.6}.table{overflow-x:auto}</style><main><h1>FREYA lokalna provjera</h1>'''
    page+='<p><b>'+esc(report['result'])+'</b></p><p>Popravljen je način prepoznavanja Excel formula. Broj uključuje i formule u audit listovima. Ova provjera ne preračunava formule i ne potvrđuje cijene ili finansijsku tačnost.</p>'
    page+='<div class="table"><table><tr><th>Fajl</th><th>Ranije formule</th><th>Sada formule</th><th>Obrada</th></tr>'+rows+'</table></div>'
    page+='<p>Raniji izvještaj ostaje sačuvan. Za isti hash fajla koristi noviji nalaz broja formula. Prethodni AI tekst zasnovan na nula formula zahtijeva ispravku.</p>'
    page+='<p>CAPEX audit list i poslovni podaci nijesu mijenjani. Pozadinski agenti nijesu pokrenuti. API pozivi: 0.</p>'
    if report.get('error'):page+='<p>Razlog zaustavljanja: '+esc(report['error'])+'</p>'
    write_new(session/'PREGLED.html',page+'</main></html>')
    paths=sorted(p for p in session.rglob('*') if p.is_file() and 'INPUT' not in p.relative_to(session).parts and 'FIXTURES' not in p.relative_to(session).parts)
    hashes={str(p.relative_to(session)):digest(stable_read(p,1024*1024)) for p in paths}
    write_json(session/'SHA256.json',hashes);paths.append(session/'SHA256.json')
    pkg=session/'IPHONE_888_LOKALNI_RESULT.zip'
    with zipfile.ZipFile(pkg,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:z.write(p,str(p.relative_to(session)))
    with zipfile.ZipFile(pkg) as z:
        if z.testzip() is not None or not all(digest(z.read(n))==h for n,h in hashes.items()):raise Hold('PACKAGE_VERIFICATION_FAILED')
    print('RESULT='+report['result'])
    print('LOCAL_TESTS_PASS='+str(sum(report.get('tests',{}).values())))
    print('REAL_FILES_PROCESSED='+str(sum(r['status']=='PROCESSED' for r in report['files'])))
    print('FORMULA_COUNT_CORRECTIONS='+str(sum(r.get('formula_count_changed',False) for r in report['files'])))
    print('API_CALLS=0 | BACKGROUND_SERVICE=NOT_STARTED')
    print('HTML='+str(session/'PREGLED.html'));print('PACKAGE='+str(pkg))
    print('PACKAGE_SHA256='+digest(stable_read(pkg,10*1024*1024)))


def prepare_repair(previous=PREVIOUS, output_base=Path('/root')):
    summary_raw=stable_read(previous/'SUMMARY.json',100000)
    if digest(summary_raw)!=SUMMARY_SHA:raise Hold('PREVIOUS_SUMMARY_HASH_MISMATCH')
    old=json.loads(summary_raw)
    if len(old.get('processed',[]))!=8:raise Hold('EXPECTED_EIGHT_INPUTS')
    # Exact previously executed module copies. Never search or execute unknown candidates.
    originals={}
    for name in MODULES:
        raw=stable_read(previous/'CODE'/name,524288)
        wanted=OLD_VALIDATOR_SHA if name=='financial_validator_v2_888.py' else MODULES[name][1]
        if digest(raw)!=wanted:raise Hold('PREVIOUS_MODULE_HASH_MISMATCH: '+name)
        originals[name]=raw
    if digest(FIXED_VALIDATOR)!=MODULES['financial_validator_v2_888.py'][1]:raise Hold('PATCH_HASH_MISMATCH')
    os.umask(0o077)
    session=Path(tempfile.mkdtemp(prefix='IPHONE_888_LOKALNI_',dir=output_base))
    print('OUTPUT='+str(session),flush=True)
    report={'protocol':'888','batch':'LOCAL-REPAIR-01','started_utc':utc(),
        'result':'HOLD','files':[],'tests':{},'api_calls':0,'background_service':'NOT_STARTED',
        'previous_summary_sha256':SUMMARY_SHA,'financial_accuracy':'NOT_ASSESSED',
        'script_sha256':digest(stable_read(Path(__file__),1024*1024)),
        'canonical_runtime_changed':False,'source_workbooks_edited':False,'error':None}
    try:
        for name,raw in originals.items():
            write_new(session/'CODE'/name,FIXED_VALIDATOR if name=='financial_validator_v2_888.py' else raw)
        write_json(session/'MODULE_LINEAGE.json',[
            {'name':name,'previous_sha256':digest(raw),'current_sha256':MODULES[name][1],
             'change':'XML_NAMESPACE_FORMULA_COUNT' if name=='financial_validator_v2_888.py' else 'UNCHANGED'} for name,raw in originals.items()])
        print('KORAK=OBJEDINJENI_LOKALNI_TESTOVI',flush=True)
        report['tests']=regression_tests(session)
        for i,prior in enumerate(old['processed'],1):
            print('KORAK=SAČUVANI_FAJL_%d_OD_8'%i,flush=True)
            record={'name':prior['source_name'],'status':'HOLD'}
            report['files'].append(record)
            try:
                suffix=Path(prior['source_name']).suffix.lower()
                src=previous/'BUSINESS'/('OBJECT_%02d'%i)/'INPUT'/('source'+suffix)
                if digest(stable_read(src))!=prior['source_sha256']:raise Hold('PREVIOUS_INPUT_HASH_MISMATCH')
                row=process_file(session,src,session/'BUSINESS'/('OBJECT_%02d'%i),'REUSED_VERIFIED_INPUT')
                record.update({'status':'PROCESSED','source_sha256':row['source_sha256'],
                    'document_processor':row['document_processor'],'xlsx_limited_check':row['xlsx_keyword_check'],
                    'source_unchanged':row['source_content_unchanged_observed']})
                if suffix=='.xlsx':
                    if row.get('xlsx_exit_code')!=0 or 'FORMULAS' not in row.get('xlsx_checks',{}):raise Hold('XLSX_PARSE_FAILED')
                    a=int(prior.get('xlsx_checks',{}).get('FORMULAS',0));b=int(row['xlsx_checks']['FORMULAS'])
                    record.update(old_formula_count=a,new_formula_count=b,formula_count_changed=a!=b)
                    if prior['source_sha256']==UNI_SHA and b!=263:raise Hold('REAL_CAPEX_REGRESSION_FAILED')
            except Exception as ex:
                record['status']='HOLD';record['reason']=str(ex) if isinstance(ex,Hold) else type(ex).__name__
        for name,raw in originals.items():
            if digest(stable_read(previous/'CODE'/name,524288))!=digest(raw):raise Hold('PREVIOUS_MODULE_CHANGED')
        if digest(stable_read(previous/'SUMMARY.json',100000))!=SUMMARY_SHA:raise Hold('PREVIOUS_SUMMARY_CHANGED')
        report['result']='LOCAL_MODULE_REPAIR_AND_TEST_PASS' if all(r['status']=='PROCESSED' for r in report['files']) else 'LOCAL_REPAIR_DONE_SOME_INPUTS_HOLD'
    except (Exception,KeyboardInterrupt) as ex:
        report['error']=str(ex) if isinstance(ex,Hold) else type(ex).__name__
    report['completed_utc']=utc();finish(session,report)
    return session,report


if __name__=='__main__':
    try:
        if sys.argv[1:]!=['--popravi-888']:
            print('PREPARED | Pokreni sa --popravi-888 | NETWORK=NONE')
        else:
            _,result=prepare_repair()
            sys.exit(0 if result['result']=='LOCAL_MODULE_REPAIR_AND_TEST_PASS' else 2)
    except (Exception,KeyboardInterrupt) as ex:
        print('RESULT=HOLD');print('REASON='+ (str(ex) if isinstance(ex,Hold) else type(ex).__name__))
        sys.exit(2)
