#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

HOME = Path.home()
FACTORY = HOME / "FREYA_SSOT_DOCUMENT_FACTORY"
SOURCES_FILE = FACTORY / "01_SOURCE_REGISTRY" / "SOURCES.tsv"

DEFAULT_CASE_TERMS = [
    "ars metal",
    "ars metal industries",
    "civil engineering",
    "civil engineering doo",
    "hala",
    "projekat hale",
    "projektant",
    "projektovanje",
    "projektna dokumentacija",
    "glavni projekat",
    "idejni projekat",
    "izvedbeni projekat",
    "ugovor",
    "aneks",
    "ponuda",
    "faktura",
    "račun",
    "racun",
    "uplata",
    "kašnjenje",
    "kasnjenje",
    "rok",
    "šteta",
    "steta",
    "gubitak",
    "dozvola",
    "urbanističko",
    "urbanisticko",
    "građevinska",
    "gradjevinska",
    "dwg",
    "cedis",
    "tuzi",
]

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".tsv", ".psv", ".json", ".xml",
    ".html", ".htm", ".log", ".ini", ".cfg", ".yaml", ".yml",
    ".sql", ".rtf"
}

DOCUMENT_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".odt", ".xlsx", ".xls", ".pptx",
    ".eml", ".msg", ".dwg", ".dxf"
}

MAX_DIRECT_TEXT_BYTES = 20 * 1024 * 1024
MAX_DOCUMENT_BYTES = 150 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 500_000
MAX_CONTENT_CANDIDATES = 5_000


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def load_sources() -> list[tuple[str, Path]]:
    sources: list[tuple[str, Path]] = []

    with SOURCES_FILE.open("r", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            path = Path(row["PATH"]).expanduser()
            if path.exists() and path.is_dir():
                sources.append((row["SOURCE_ID"], path))

    return sources


def safe_stat(path: Path):
    try:
        return path.stat()
    except (OSError, PermissionError):
        return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    try:
        with path.open("rb") as handle:
            while True:
                block = handle.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        return digest.hexdigest()
    except (OSError, PermissionError):
        return ""


def read_plain_text(path: Path) -> str:
    stat = safe_stat(path)
    if stat is None or stat.st_size > MAX_DIRECT_TEXT_BYTES:
        return ""

    try:
        data = path.read_bytes()
    except (OSError, PermissionError):
        return ""

    for encoding in ("utf-8", "utf-16", "cp1250", "latin-1"):
        try:
            return data.decode(encoding, errors="strict")[:MAX_EXTRACTED_CHARACTERS]
        except UnicodeError:
            continue

    return data.decode("utf-8", errors="replace")[:MAX_EXTRACTED_CHARACTERS]


def read_docx(path: Path) -> str:
    stat = safe_stat(path)
    if stat is None or stat.st_size > MAX_DOCUMENT_BYTES:
        return ""

    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = set(archive.namelist())
            if "word/document.xml" not in names:
                return ""

            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
            text = re.sub(r"</w:p[^>]*>", "\n", xml)
            text = re.sub(r"<w:tab[^>]*/>", "\t", text)
            text = re.sub(r"<[^>]+>", "", text)
            return html.unescape(text)[:MAX_EXTRACTED_CHARACTERS]
    except (OSError, PermissionError, zipfile.BadZipFile, KeyError):
        return ""


def read_pdf(path: Path) -> str:
    stat = safe_stat(path)
    if stat is None or stat.st_size > MAX_DOCUMENT_BYTES:
        return ""

    if shutil.which("pdftotext") is None:
        return ""

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=120,
            check=False,
        )
        return result.stdout.decode("utf-8", errors="replace")[:MAX_EXTRACTED_CHARACTERS]
    except (OSError, subprocess.TimeoutExpired):
        return ""


def extract_text(path: Path) -> str:
    suffix = path.suffix.casefold()

    if suffix in TEXT_EXTENSIONS:
        return read_plain_text(path)
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)

    return ""


def matched_terms(value: str, terms: list[str]) -> list[str]:
    normalized = normalize(value)
    return sorted({term for term in terms if normalize(term) in normalized})


def walk_source(source_id: str, root: Path) -> Iterable[Path]:
    excluded_names = {
        "$recycle.bin",
        "system volume information",
        "windows",
        "program files",
        "program files (x86)",
        "programdata",
        "appdata",
        ".cache",
        ".local/share/trash",
        "node_modules",
        ".git",
    }

    def onerror(error: OSError) -> None:
        return

    for current_root, dirs, files in os.walk(root, topdown=True, onerror=onerror, followlinks=False):
        current_path = Path(current_root)
        lowered = normalize(str(current_path))

        dirs[:] = [
            name for name in dirs
            if normalize(name) not in excluded_names
            and "/appdata/" not in lowered
            and "\\appdata\\" not in lowered
        ]

        for filename in files:
            yield current_path / filename


def create_case(case_name: str, extra_terms: list[str]) -> int:
    run_id = now_id()
    safe_case = re.sub(r"[^A-Za-z0-9_.-]+", "_", case_name).strip("_") or "CASE"
    case_dir = FACTORY / "02_CASES" / f"{safe_case}_{run_id}"

    dirs = {
        "control": case_dir / "00_CONTROL",
        "evidence": case_dir / "01_EVIDENCE",
        "extracted": case_dir / "02_EXTRACTED_TEXT",
        "analysis": case_dir / "03_ANALYSIS",
        "drafts": case_dir / "04_DRAFTS",
        "review": case_dir / "05_HUMAN_GATE_REVIEW",
        "logs": case_dir / "06_LOGS",
    }

    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    terms = sorted(set(DEFAULT_CASE_TERMS + [normalize(t) for t in extra_terms if t.strip()]))
    sources = load_sources()

    if not sources:
        print("FINAL_STATUS=BLOCKED_NO_REGISTERED_SOURCES")
        return 1

    (dirs["control"] / "CASE_SPECIFICATION.txt").write_text(
        "\n".join([
            f"CASE_ID={safe_case}_{run_id}",
            f"CASE_NAME={case_name}",
            "PURPOSE=EVIDENCE_BASED_CORRESPONDENCE_FACTORY",
            "HUMAN_GATE=Danijela_Djurovic_Keskin",
            "ORIGINALS_CHANGED=NO",
            "DOCUMENTS_SENT=NO",
            "DOCUMENTS_PUBLISHED=NO",
            "",
            "SEARCH_TERMS:",
            *[f"- {term}" for term in terms],
            "",
        ]),
        encoding="utf-8",
    )

    database_path = dirs["evidence"] / "CASE_EVIDENCE.sqlite"
    connection = sqlite3.connect(database_path)

    connection.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            size_bytes INTEGER,
            modified_time TEXT,
            filename_terms TEXT,
            content_terms TEXT,
            sha256 TEXT,
            extraction_status TEXT,
            local_text_path TEXT
        );

        CREATE VIRTUAL TABLE evidence_fts USING fts5(
            evidence_id,
            filename,
            source_path,
            extracted_text
        );
    """)

    register_path = dirs["evidence"] / "EVIDENCE_REGISTER.tsv"
    errors_path = dirs["logs"] / "READ_ERRORS.tsv"
    candidates: list[tuple[str, Path, list[str]]] = []

    total_seen = 0
    filename_hits = 0

    with register_path.open("w", encoding="utf-8", newline="") as register, \
         errors_path.open("w", encoding="utf-8", newline="") as errors:

        writer = csv.writer(register, delimiter="\t")
        error_writer = csv.writer(errors, delimiter="\t")

        writer.writerow([
            "EVIDENCE_ID", "SOURCE_ID", "SOURCE_PATH", "FILENAME",
            "EXTENSION", "SIZE_BYTES", "MODIFIED_TIME",
            "FILENAME_TERMS", "CONTENT_TERMS", "SHA256",
            "EXTRACTION_STATUS", "LOCAL_TEXT_PATH"
        ])
        error_writer.writerow(["SOURCE_ID", "PATH", "ERROR"])

        sequence = 0

        for source_id, root in sources:
            print(f"SOURCE_SCAN_START={source_id}|{root}", flush=True)

            for path in walk_source(source_id, root):
                total_seen += 1

                if total_seen % 100000 == 0:
                    print(f"SCAN_PROGRESS=FILES_SEEN:{total_seen}|FILENAME_HITS:{filename_hits}", flush=True)

                filename_match = matched_terms(str(path), terms)
                suffix = path.suffix.casefold()

                if not filename_match:
                    continue

                filename_hits += 1
                candidates.append((source_id, path, filename_match))

                if len(candidates) >= MAX_CONTENT_CANDIDATES:
                    print(f"CANDIDATE_LIMIT_REACHED={MAX_CONTENT_CANDIDATES}", flush=True)
                    break

            if len(candidates) >= MAX_CONTENT_CANDIDATES:
                break

        print(f"CONTENT_EXTRACTION_CANDIDATES={len(candidates)}", flush=True)

        for source_id, path, filename_match in candidates:
            sequence += 1
            evidence_id = f"EV-{sequence:06d}"
            stat = safe_stat(path)

            if stat is None:
                error_writer.writerow([source_id, str(path), "STAT_FAILED"])
                continue

            extracted = ""
            extraction_status = "NOT_SUPPORTED"
            local_text_path = ""

            try:
                extracted = extract_text(path)

                if extracted:
                    extraction_status = "TEXT_EXTRACTED"
                    local_path = dirs["extracted"] / f"{evidence_id}.txt"
                    local_path.write_text(
                        f"EVIDENCE_ID={evidence_id}\n"
                        f"SOURCE_ID={source_id}\n"
                        f"SOURCE_PATH={path}\n\n"
                        f"{extracted}",
                        encoding="utf-8",
                        errors="replace",
                    )
                    local_text_path = str(local_path)
                elif path.suffix.casefold() in TEXT_EXTENSIONS | {".docx", ".pdf"}:
                    extraction_status = "EXTRACTION_EMPTY_OR_FAILED"

                content_match = matched_terms(extracted, terms) if extracted else []
                digest = file_sha256(path)

                modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

                row = [
                    evidence_id,
                    source_id,
                    str(path),
                    path.name,
                    path.suffix.casefold(),
                    stat.st_size,
                    modified,
                    "|".join(filename_match),
                    "|".join(content_match),
                    digest,
                    extraction_status,
                    local_text_path,
                ]

                writer.writerow(row)

                connection.execute(
                    """
                    INSERT INTO evidence (
                        evidence_id, source_id, source_path, filename,
                        extension, size_bytes, modified_time,
                        filename_terms, content_terms, sha256,
                        extraction_status, local_text_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    row,
                )

                connection.execute(
                    """
                    INSERT INTO evidence_fts (
                        evidence_id, filename, source_path, extracted_text
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (evidence_id, path.name, str(path), extracted),
                )

            except Exception as error:
                error_writer.writerow([source_id, str(path), repr(error)])

    connection.commit()

    chronology_path = dirs["analysis"] / "CHRONOLOGY.tsv"
    with chronology_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["MODIFIED_TIME", "EVIDENCE_ID", "SOURCE_ID", "FILENAME", "SOURCE_PATH"])

        for row in connection.execute(
            """
            SELECT modified_time, evidence_id, source_id, filename, source_path
            FROM evidence
            ORDER BY modified_time ASC
            """
        ):
            writer.writerow(row)

    recipient_map = dirs["analysis"] / "RECIPIENT_AUTHORITY_MAP.tsv"
    recipient_map.write_text(
        "\n".join([
            "RECIPIENT_ID\tINSTITUTION\tPURPOSE\tSTATUS",
            "REC-001\tVlada Crne Gore / Generalni sekretarijat\tInstitucionalno upoznavanje i koordinacija\tPROPOSED",
            "REC-002\tMinistarstvo prostornog planiranja, urbanizma i državne imovine\tProjektna dokumentacija i odgovornost učesnika u građenju\tPROPOSED",
            "REC-003\tMinistarstvo ekonomskog razvoja\tUticaj na investiciju i poslovanje\tPROPOSED",
            "REC-004\tMinistarstvo finansija\tFinansijske posljedice po investiciju\tPROPOSED",
            "REC-005\tMinistarstvo pravde\tPravna zaštita i nadležni mehanizmi\tPROPOSED",
            "",
        ]),
        encoding="utf-8",
    )

    missing = dirs["analysis"] / "MISSING_EVIDENCE_REGISTER.tsv"
    missing.write_text(
        "\n".join([
            "MISSING_ID\tREQUIRED_ITEM\tSTATUS",
            "MISS-001\tPotpisani osnovni ugovor sa Civil Engineering DOO\tTO_VERIFY",
            "MISS-002\tSvi aneksi ugovora\tTO_VERIFY",
            "MISS-003\tDokaz ugovorenih rokova\tTO_VERIFY",
            "MISS-004\tDokaz stvarnih datuma predaje projektne dokumentacije\tTO_VERIFY",
            "MISS-005\tKompletna poslovna prepiska i upozorenja\tTO_VERIFY",
            "MISS-006\tFakture i dokazi plaćanja\tTO_VERIFY",
            "MISS-007\tObračun direktne i indirektne finansijske štete\tTO_VERIFY",
            "MISS-008\tDozvole, saglasnosti i relevantna projektna dokumentacija\tTO_VERIFY",
            "MISS-009\tPravna analiza odgovornosti projektanta\tLEGAL_REVIEW_REQUIRED",
            "",
        ]),
        encoding="utf-8",
    )

    evidence_rows = list(connection.execute(
        """
        SELECT evidence_id, filename, source_path, modified_time,
               filename_terms, content_terms
        FROM evidence
        ORDER BY modified_time ASC
        LIMIT 250
        """
    ))

    evidence_summary = "\n".join(
        f"- [{row[0]}] {row[1]} | {row[3]} | {row[2]}"
        for row in evidence_rows
    )

    base_letter = f"""DRAFT_FOR_HUMAN_GATE_REVIEW
NOT_SENT
NOT_PUBLISHED
LEGAL_REVIEW_PENDING

ARS METAL INDUSTRIES DOO
Podgorica

PRIMALAC:
[ODABRATI IZ RECIPIENT_AUTHORITY_MAP.tsv]

PREDMET:
Zahtjev za institucionalno razmatranje činjenica i posljedica povezanih
sa projektovanjem industrijske hale i postupanjem društva Civil Engineering DOO

Poštovani,

ARS Metal Industries DOO obraća se radi institucionalnog razmatranja
činjenica i posljedica povezanih sa pripremom i predajom projektne
dokumentacije za planiranu industrijsku halu.

Ovaj dokument je automatski formiran iz SSOT Document Factory evidencije.
Sve činjenice moraju biti potvrđene u priloženom Evidence Registeru prije
potpisivanja ili slanja.

1. ČINJENIČNI OKVIR

[EVIDENCE_REQUIRED: unijeti samo činjenice potvrđene dokazima]

2. HRONOLOGIJA

Koristiti:
03_ANALYSIS/CHRONOLOGY.tsv

3. POSLJEDICE PO INVESTICIJU I POSLOVANJE

[EVIDENCE_REQUIRED: finansijski iznosi, rokovi i uzročna veza moraju biti
potvrđeni dokumentacijom i stručnim pregledom]

4. ZAHTJEV INSTITUCIJI

Molimo da, u okviru svojih nadležnosti:

a) razmotrite dostavljene činjenice i dokumentaciju;
b) obavijestite ARS Metal Industries DOO o nadležnim postupcima;
c) navedete instituciju ili organ nadležan za svako pitanje koje nije u
   vašoj neposrednoj nadležnosti;
d) dostavite odgovor u zakonskom ili drugom primjenjivom roku.

5. PRILOZI

- EVIDENCE_REGISTER.tsv
- CHRONOLOGY.tsv
- RECIPIENT_AUTHORITY_MAP.tsv
- MISSING_EVIDENCE_REGISTER.tsv
- pojedinačni dokazi odabrani nakon Human Gate pregleda

S poštovanjem,

Danijela Đurović Keskin
ARS Metal Industries DOO

EVIDENCE ORIENTATION — FIRST REGISTERED ITEMS

{evidence_summary if evidence_summary else "[NO_EVIDENCE_ITEMS_REGISTERED]"}
"""

    (dirs["drafts"] / "MASTER_LETTER_DRAFT.txt").write_text(
        base_letter,
        encoding="utf-8",
    )

    recipient_drafts = [
        ("01_VLADA_CRNE_GORE.txt", "Vlada Crne Gore / Generalni sekretarijat"),
        ("02_MINISTARSTVO_PROSTORNOG_PLANIRANJA.txt", "Ministarstvo prostornog planiranja, urbanizma i državne imovine"),
        ("03_MINISTARSTVO_EKONOMSKOG_RAZVOJA.txt", "Ministarstvo ekonomskog razvoja"),
        ("04_MINISTARSTVO_FINANSIJA.txt", "Ministarstvo finansija"),
        ("05_MINISTARSTVO_PRAVDE.txt", "Ministarstvo pravde"),
    ]

    recipient_dir = dirs["drafts"] / "RECIPIENT_DRAFTS"
    recipient_dir.mkdir(parents=True, exist_ok=True)

    for filename, institution in recipient_drafts:
        text = base_letter.replace(
            "[ODABRATI IZ RECIPIENT_AUTHORITY_MAP.tsv]",
            institution,
        )
        (recipient_dir / filename).write_text(text, encoding="utf-8")

    review = dirs["review"] / "HUMAN_GATE_REVIEW_REPORT.txt"
    error_count = sum(1 for _ in errors_path.open("r", encoding="utf-8", errors="replace")) - 1

    review.write_text(
        "\n".join([
            "HUMAN_GATE_REVIEW_REPORT",
            f"CASE={safe_case}_{run_id}",
            f"FILES_SEEN={total_seen}",
            f"FILENAME_HITS={filename_hits}",
            f"EVIDENCE_ITEMS_REGISTERED={len(candidates)}",
            f"READ_ERRORS={max(error_count, 0)}",
            "ORIGINALS_CHANGED=NO",
            "SOURCE_FILES_DELETED=NO",
            "SOURCE_FILES_MOVED=NO",
            "SOURCE_FILES_RENAMED=NO",
            "DOCUMENTS_SENT=NO",
            "DOCUMENTS_PUBLISHED=NO",
            "LEGAL_REVIEW_PENDING=YES",
            "FINAL_STATUS=HUMAN_REVIEW_READY",
            f"CASE_DIRECTORY={case_dir}",
            "",
        ]),
        encoding="utf-8",
    )

    pointer = FACTORY / "00_CONTROL" / "CURRENT_CASE.txt"
    pointer.write_text(str(case_dir) + "\n", encoding="utf-8")

    connection.close()

    print("")
    print("============================================================")
    print("FREYA_SSOT_DOCUMENT_FACTORY_CASE_COMPLETE")
    print("============================================================")
    print(f"CASE_DIRECTORY={case_dir}")
    print(f"FILES_SEEN={total_seen}")
    print(f"FILENAME_HITS={filename_hits}")
    print(f"EVIDENCE_ITEMS_REGISTERED={len(candidates)}")
    print(f"EVIDENCE_REGISTER={register_path}")
    print(f"CHRONOLOGY={chronology_path}")
    print(f"RECIPIENT_MAP={recipient_map}")
    print(f"MASTER_DRAFT={dirs['drafts'] / 'MASTER_LETTER_DRAFT.txt'}")
    print(f"HUMAN_GATE_REPORT={review}")
    print("ORIGINALS_CHANGED=NO")
    print("DOCUMENTS_SENT=NO")
    print("DOCUMENTS_PUBLISHED=NO")
    print("FINAL_STATUS=HUMAN_REVIEW_READY")
    return 0


def status() -> int:
    pointer = FACTORY / "00_CONTROL" / "CURRENT_CASE.txt"

    print("FREYA_SSOT_DOCUMENT_FACTORY_STATUS")
    print(f"FACTORY={FACTORY}")
    print(f"ENGINE_EXISTS={'YES' if Path(__file__).exists() else 'NO'}")
    print(f"SOURCES_REGISTERED={'YES' if SOURCES_FILE.exists() else 'NO'}")
    print(f"CURRENT_CASE={pointer.read_text(encoding='utf-8').strip() if pointer.exists() else 'NONE'}")
    print("HUMAN_GATE=ACTIVE")
    print("AUTO_SEND=NO")
    print("PUBLICATION=NO")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="factory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status")

    case_parser = subparsers.add_parser("case")
    case_parser.add_argument("case_name")
    case_parser.add_argument("terms", nargs="*")

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("document_type")
    create_parser.add_argument("case_name")
    create_parser.add_argument("terms", nargs="*")

    args = parser.parse_args()

    if args.command == "status":
        return status()

    if args.command == "case":
        return create_case(args.case_name, args.terms)

    if args.command == "create":
        if normalize(args.document_type) not in {"letters", "dopisi", "letter"}:
            print("FINAL_STATUS=BLOCKED_UNSUPPORTED_DOCUMENT_TYPE")
            return 2
        return create_case(args.case_name, args.terms)

    return 2


if __name__ == "__main__":
    sys.exit(main())
