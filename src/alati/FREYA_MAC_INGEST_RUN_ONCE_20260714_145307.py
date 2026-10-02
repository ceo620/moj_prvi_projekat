from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

HUMAN_GATE = "Danijela_Djurovic_Keskin"
PROTOKOL = "888"

FACTORY = Path(sys.argv[1])
RUN_ID = sys.argv[2]

MOUNT = FACTORY.parent
HOME = Path.home()

RAW = FACTORY / "03_RAW_BY_DEVICE" / "01_MAC"
ADAPTER = FACTORY / "02_DEVICE_ADAPTERS" / "01_MAC"
LIVE = FACTORY / "16_LIVE_FREYA_HOME"
DYNAMIC = FACTORY / "15_DYNAMIC_CATEGORY_SYSTEM"

UNIQUE_ROOT = FACTORY / "05_UNIQUE_CONTENT" / "SHA256"
GLOBAL_LINEAGE = FACTORY / "04_SHA256_AND_LINEAGE"
GLOBAL_DUPLICATES = FACTORY / "06_DUPLICATE_HASH_MAP"
GLOBAL_LINKS = FACTORY / "07_SCRIPT_DOCTRINE_LINKS"
GLOBAL_RECEIPTS = FACTORY / "11_TRANSFER_RECEIPTS"
GLOBAL_REPORTS = FACTORY / "14_REPORTS_AND_RECOVERY"

STATUS_FILE = LIVE / "LIVE_STATUS.env"
EVENT_FILE = LIVE / "EVENT_STREAM.log"
WORKER_STATUS = ADAPTER / "00_CONTROL" / "WORKER_STATUS.txt"
LOCK_DIR = ADAPTER / "00_CONTROL" / "MAC_INGEST_ACTIVE.lock"

RUN_REPORT = GLOBAL_REPORTS / f"MAC_INGEST_{RUN_ID}"
RUN_REPORT.mkdir(parents=True, exist_ok=False)

SOURCE_REGISTER = (
    RAW
    / "07_SOURCE_PATH_REGISTER"
    / f"MAC_SOURCE_PATH_REGISTER_{RUN_ID}.tsv"
)

DEVICE_SHA_MANIFEST = (
    RAW
    / "08_SHA256_MANIFEST"
    / f"MAC_SHA256_MANIFEST_{RUN_ID}.tsv"
)

GLOBAL_SHA_MANIFEST = (
    GLOBAL_LINEAGE
    / f"MAC_SHA256_LINEAGE_{RUN_ID}.tsv"
)

DEVICE_DUPLICATE_MAP = (
    RAW
    / "09_DUPLICATE_MAP"
    / f"MAC_DUPLICATE_PATH_MAP_{RUN_ID}.tsv"
)

GLOBAL_DUPLICATE_MAP = (
    GLOBAL_DUPLICATES
    / f"MAC_DUPLICATE_PATH_MAP_{RUN_ID}.tsv"
)

SENSITIVE_REGISTER = (
    RAW
    / "15_SENSITIVE_REVIEW_REQUIRED"
    / f"MAC_SENSITIVE_METADATA_ONLY_{RUN_ID}.tsv"
)

ERROR_REPORT = RUN_REPORT / "01_ERRORS.tsv"
SUMMARY_REPORT = RUN_REPORT / "02_SUMMARY.txt"
SCOPE_REPORT = RUN_REPORT / "03_SOURCE_SCOPE.txt"
GAP_REPORT = (
    RAW
    / "12_DEVICE_GAP_REGISTER"
    / f"MAC_DEVICE_GAP_REGISTER_{RUN_ID}.txt"
)

RECEIPT = (
    GLOBAL_RECEIPTS
    / f"MAC_INGEST_RECEIPT_{RUN_ID}.txt"
)

LINK_REPORT = (
    GLOBAL_LINKS
    / f"MAC_SCRIPT_DOCTRINE_CANDIDATE_LINKS_{RUN_ID}.tsv"
)

PROPOSAL_REPORT = (
    DYNAMIC
    / "02_CATEGORY_PROPOSALS"
    / f"MAC_CATEGORY_PROPOSALS_{RUN_ID}.tsv"
)

DEVICE_PROPOSAL_POINTER = (
    RAW
    / "16_CATEGORY_PROPOSALS"
    / f"MAC_CATEGORY_PROPOSAL_POINTER_{RUN_ID}.txt"
)

CATEGORY_PATHS = {
    "SCRIPTS_RAW": RAW / "01_SCRIPTS_RAW",
    "DOCTRINES_README_SPECS": RAW / "02_DOCTRINES_README_SPECS",
    "CONFIG_AND_DEPENDENCIES": RAW / "03_CONFIG_AND_DEPENDENCIES",
    "TESTS_LOGS_AND_EXAMPLES": RAW / "04_TESTS_LOGS_AND_EXAMPLES",
    "DOCUMENTATION": RAW / "05_DOCUMENTATION",
    "ARCHIVES_PENDING_REVIEW": RAW / "06_ARCHIVES_PENDING_REVIEW",
    "REVIEW_REQUIRED": RAW / "11_REVIEW_REQUIRED",
}

for path in [
    SOURCE_REGISTER.parent,
    DEVICE_SHA_MANIFEST.parent,
    GLOBAL_SHA_MANIFEST.parent,
    DEVICE_DUPLICATE_MAP.parent,
    GLOBAL_DUPLICATE_MAP.parent,
    SENSITIVE_REGISTER.parent,
    GAP_REPORT.parent,
    RECEIPT.parent,
    LINK_REPORT.parent,
    PROPOSAL_REPORT.parent,
    DEVICE_PROPOSAL_POINTER.parent,
    UNIQUE_ROOT,
]:
    path.mkdir(parents=True, exist_ok=True)

for path in CATEGORY_PATHS.values():
    path.mkdir(parents=True, exist_ok=True)

if not STATUS_FILE.is_file():
    print("FINAL_STATUS=BLOCKED_LIVE_STATUS_NOT_FOUND")
    raise SystemExit(10)

if LOCK_DIR.exists():
    print(f"ACTIVE_LOCK={LOCK_DIR}")
    print("FINAL_STATUS=BLOCKED_MAC_INGEST_LOCK_ALREADY_EXISTS")
    raise SystemExit(11)

LOCK_DIR.mkdir(parents=True, exist_ok=False)

start_monotonic = time.monotonic()
started_at = datetime.now().isoformat(timespec="seconds")

SCRIPT_EXTENSIONS = {
    ".sh", ".bash", ".zsh", ".fish",
    ".py", ".pyw",
    ".js", ".mjs", ".cjs", ".jsx",
    ".ts", ".tsx",
    ".ps1", ".psm1", ".psd1",
    ".bat", ".cmd", ".vbs",
    ".rb", ".pl", ".php", ".lua",
    ".go", ".rs",
    ".java", ".kt", ".kts",
    ".swift",
    ".c", ".h", ".cpp", ".hpp", ".cc",
    ".cs", ".sql", ".r",
}

DOCUMENT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".rtf",
    ".pdf", ".doc", ".docx", ".odt",
    ".xls", ".xlsx", ".ods", ".csv", ".tsv",
    ".ppt", ".pptx", ".odp",
}

CONFIG_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".conf", ".config",
    ".env", ".lock", ".properties",
    ".plist", ".xml",
}

ARCHIVE_EXTENSIONS = {
    ".zip", ".7z", ".rar",
    ".tar", ".tgz", ".gz", ".bz2", ".xz",
    ".dmg", ".iso",
}

SCRIPT_NAMES = {
    "makefile", "dockerfile", "justfile",
    "rakefile", "gemfile", "procfile",
}

CONFIG_NAMES = {
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "cargo.toml",
    "cargo.lock",
    "go.mod",
    "go.sum",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}

DOCTRINE_SIGNALS = {
    "doctrine", "doktrina", "readme",
    "architecture", "arhitektura",
    "specification", "specifikacija",
    "protocol", "protokol",
    "governance", "upravljanje",
    "policy", "politika",
    "rules", "pravila",
    "manual", "guide", "vodic",
    "strategy", "strategija",
    "framework", "concept",
    "ssot", "sop",
}

TEST_SIGNALS = {
    "test", "tests", "testing",
    "spec", "specs",
    "example", "examples",
    "sample", "samples",
    "fixture", "fixtures",
    "expected", "result",
    "log", "logs",
}

HIGH_SIGNAL_TERMS = {
    "freya", "titan", "ssot",
    "script", "skript",
    "doctrine", "doktrina",
    "human_gate", "human gate",
    "protokol_888", "protocol_888",
    "control_room", "control room",
    "data_room", "data room",
    "evidence", "audit",
    "ingest", "adapter", "daemon",
}

STRONG_SENSITIVE_PATH_SIGNALS = {
    "wallet",
    "seed_phrase", "seed phrase",
    "mnemonic",
    "private_key", "private key",
    "id_rsa", "id_ed25519",
    "keychain",
    "passwords", "password database",
    "credentials",
    "keystore",
    "kdbx",
    "cookies",
    "login data",
    "browser profile",
}

TOPIC_PROPOSALS = {
    "KERNEL_DRIVERS_AND_HARDWARE_RECOVERY": {
        "kernel", "driver", "firmware", "hardware",
        "gpu", "cuda", "bios",
    },
    "LEGAL_CASES_AND_CONTRACTS": {
        "legal", "contract", "ugovor",
        "annex", "aneks", "court", "case",
    },
    "FINANCIAL_STRUCTURING_AND_CAPITAL": {
        "finance", "financial", "capital",
        "bank", "invoice", "loan", "27.8m",
    },
    "REGULATORY_ESG_AND_COMPLIANCE": {
        "regulation", "regulatory", "compliance",
        "taxonomy", "esg", "eu directive",
    },
    "DEVICE_ADAPTERS_AND_BOOTSTRAP": {
        "adapter", "bootstrap", "termux",
        "ish", "launchd", "systemd",
    },
    "RECOVERY_RESTORE_AND_REPAIR": {
        "recovery", "restore", "repair",
        "rescue", "revival",
    },
}

SKIP_DIRECTORY_NAMES = {
    "Library",
    "Applications",
    "Movies",
    "Music",
    "Pictures",
    "Public",
    ".Trash",
    ".cache",
    ".npm",
    ".gradle",
    ".m2",
    ".cargo",
    ".rustup",
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "DerivedData",
    "Caches",
    "FREYA_RED_MOUNT_888",
}

SKIP_DIRECTORY_SUFFIXES = {
    ".app",
    ".photoslibrary",
    ".photolibrary",
    ".framework",
    ".bundle",
    ".dSYM",
    ".xcarchive",
}

TEXT_SAMPLE_EXTENSIONS = (
    SCRIPT_EXTENSIONS
    | CONFIG_EXTENSIONS
    | {".txt", ".md", ".markdown", ".rst", ".log", ".csv", ".tsv"}
)

category_handles: Dict[str, object] = {}
validated_existing_objects: Set[str] = set()
seen_hash_paths: Dict[str, str] = {}

scripts: List[Tuple[Path, str]] = []
doctrines: List[Tuple[Path, str]] = []
proposal_hits: Dict[str, Dict[str, object]] = {}

files_examined = 0
directories_examined = 0
low_signal_skipped = 0
valuable_discovered = 0
discovered_bytes = 0
copied_verified = 0
copied_bytes = 0
unique_objects = 0
duplicate_paths = 0
scripts_classified = 0
doctrines_classified = 0
configs_classified = 0
tests_classified = 0
documentation_classified = 0
archives_held = 0
review_required = 0
sensitive_required = 0
hash_mismatches = 0
copy_errors = 0
scan_errors = 0
script_doctrine_links = 0

base_status: Dict[str, str] = {}


def sanitize(value: object) -> str:
    return (
        str(value)
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def parse_status() -> Dict[str, str]:
    result: Dict[str, str] = {}

    for line in STATUS_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()

    return result


def int_status(key: str) -> int:
    try:
        return int(base_status.get(key, "0"))
    except ValueError:
        return 0


def write_status(
    phase: str,
    current_path: str = "NONE",
    current_category: str = "NONE",
    last_arrival: Optional[str] = None,
    last_event: Optional[str] = None,
    final_status: Optional[str] = None,
) -> None:
    elapsed = max(time.monotonic() - start_monotonic, 0.001)
    free_gib = shutil.disk_usage(MOUNT).free / 1024**3

    status = dict(base_status)

    status.update({
        "SCHEMA_VERSION": status.get("SCHEMA_VERSION", "1"),
        "UPDATED_AT": datetime.now().isoformat(timespec="seconds"),
        "HEARTBEAT_STATE": (
            "MAC_INGEST_RUNNING"
            if final_status is None
            else "MAC_INGEST_FINISHED"
        ),
        "CURRENT_DEVICE": "01_MAC",
        "CURRENT_PHASE": phase,
        "CURRENT_SOURCE_PATH": sanitize(current_path),
        "CURRENT_CATEGORY": sanitize(current_category),
        "MAC_STATE": (
            "RUNNING"
            if final_status is None
            else status.get("MAC_STATE", "FINISHED")
        ),
        "SOURCE_FILES_DISCOVERED": str(
            int_status("SOURCE_FILES_DISCOVERED")
            + valuable_discovered
        ),
        "SOURCE_BYTES_DISCOVERED": str(
            int_status("SOURCE_BYTES_DISCOVERED")
            + discovered_bytes
        ),
        "FILES_COPIED_VERIFIED": str(
            int_status("FILES_COPIED_VERIFIED")
            + copied_verified
        ),
        "BYTES_COPIED_VERIFIED": str(
            int_status("BYTES_COPIED_VERIFIED")
            + copied_bytes
        ),
        "SCRIPTS_CLASSIFIED": str(
            int_status("SCRIPTS_CLASSIFIED")
            + scripts_classified
        ),
        "DOCTRINES_CLASSIFIED": str(
            int_status("DOCTRINES_CLASSIFIED")
            + doctrines_classified
        ),
        "CONFIGS_CLASSIFIED": str(
            int_status("CONFIGS_CLASSIFIED")
            + configs_classified
        ),
        "TESTS_LOGS_EXAMPLES_CLASSIFIED": str(
            int_status("TESTS_LOGS_EXAMPLES_CLASSIFIED")
            + tests_classified
        ),
        "DOCUMENTATION_CLASSIFIED": str(
            int_status("DOCUMENTATION_CLASSIFIED")
            + documentation_classified
        ),
        "ARCHIVES_HELD": str(
            int_status("ARCHIVES_HELD")
            + archives_held
        ),
        "UNIQUE_SHA256_OBJECTS": str(
            int_status("UNIQUE_SHA256_OBJECTS")
            + unique_objects
        ),
        "DUPLICATE_PATHS_MAPPED": str(
            int_status("DUPLICATE_PATHS_MAPPED")
            + duplicate_paths
        ),
        "SCRIPT_DOCTRINE_LINKS": str(
            int_status("SCRIPT_DOCTRINE_LINKS")
            + script_doctrine_links
        ),
        "NEW_CATEGORY_PROPOSALS": str(
            int_status("NEW_CATEGORY_PROPOSALS")
            + len(proposal_hits)
        ),
        "REVIEW_REQUIRED": str(
            int_status("REVIEW_REQUIRED")
            + review_required
            + scan_errors
        ),
        "SENSITIVE_REVIEW_REQUIRED": str(
            int_status("SENSITIVE_REVIEW_REQUIRED")
            + sensitive_required
        ),
        "HASH_MISMATCHES": str(
            int_status("HASH_MISMATCHES")
            + hash_mismatches
        ),
        "COPY_ERRORS": str(
            int_status("COPY_ERRORS")
            + copy_errors
        ),
        "SOURCE_FILES_DELETED": status.get(
            "SOURCE_FILES_DELETED",
            "0",
        ),
        "SCAN_RATE_FILES_PER_SECOND": f"{files_examined / elapsed:.2f}",
        "COPY_RATE_MIB_PER_SECOND": f"{copied_bytes / 1024**2 / elapsed:.2f}",
        "ELAPSED_SECONDS": str(int(elapsed)),
        "FREE_GIB": f"{free_gib:.3f}",
        "LAST_ARRIVAL": sanitize(
            last_arrival
            if last_arrival is not None
            else status.get("LAST_ARRIVAL", "NONE")
        ),
        "LAST_EVENT": sanitize(
            last_event
            if last_event is not None
            else status.get("LAST_EVENT", "MAC_INGEST_RUNNING")
        ),
        "FINAL_STATUS": (
            final_status
            if final_status is not None
            else "MAC_INGEST_RUNNING"
        ),
    })

    preferred_order = [
        "SCHEMA_VERSION",
        "UPDATED_AT",
        "HEARTBEAT_STATE",
        "CURRENT_DEVICE",
        "CURRENT_PHASE",
        "CURRENT_SOURCE_PATH",
        "CURRENT_CATEGORY",
        "DEVICES_EXPECTED",
        "DEVICES_HOME_VERIFIED",
        "MAC_STATE",
        "ANDROID_STATE",
        "IPHONE_ISH_STATE",
        "LENOVO_STATE",
        "MSI_STATE",
        "ASUS_STATE",
        "SOURCE_FILES_DISCOVERED",
        "SOURCE_BYTES_DISCOVERED",
        "FILES_COPIED_VERIFIED",
        "BYTES_COPIED_VERIFIED",
        "SCRIPTS_CLASSIFIED",
        "DOCTRINES_CLASSIFIED",
        "CONFIGS_CLASSIFIED",
        "TESTS_LOGS_EXAMPLES_CLASSIFIED",
        "DOCUMENTATION_CLASSIFIED",
        "ARCHIVES_HELD",
        "UNIQUE_SHA256_OBJECTS",
        "DUPLICATE_PATHS_MAPPED",
        "SCRIPT_DOCTRINE_LINKS",
        "NEW_CATEGORY_PROPOSALS",
        "REVIEW_REQUIRED",
        "SENSITIVE_REVIEW_REQUIRED",
        "HASH_MISMATCHES",
        "COPY_ERRORS",
        "SOURCE_FILES_DELETED",
        "SCAN_RATE_FILES_PER_SECOND",
        "COPY_RATE_MIB_PER_SECOND",
        "ELAPSED_SECONDS",
        "FREE_GIB",
        "LAST_ARRIVAL",
        "LAST_EVENT",
        "FINAL_STATUS",
    ]

    ordered_keys = preferred_order + sorted(
        key
        for key in status
        if key not in preferred_order
    )

    temp = STATUS_FILE.with_name(
        f".LIVE_STATUS_{RUN_ID}.tmp"
    )

    with temp.open("w", encoding="utf-8") as handle:
        for key in ordered_keys:
            if key in status:
                handle.write(
                    f"{key}={sanitize(status[key])}\n"
                )

        handle.flush()
        os.fsync(handle.fileno())

    os.replace(temp, STATUS_FILE)


def append_event(event: str, detail: str) -> None:
    with EVENT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{datetime.now().isoformat(timespec='seconds')}\t"
            f"01_MAC\t{sanitize(event)}\t{sanitize(detail)}\n"
        )


def write_worker_status(state: str, final: str = "PENDING") -> None:
    WORKER_STATUS.write_text(
        "\n".join([
            "DEVICE=01_MAC",
            f"HUMAN_GATE={HUMAN_GATE}",
            f"PROTOKOL={PROTOKOL}",
            f"RUN_ID={RUN_ID}",
            f"WORKER_STATE={state}",
            "COPY_ONLY=YES",
            "SOURCE_DELETE=NO",
            "SOURCE_MOVE=NO",
            "SOURCE_RENAME=NO",
            "SCRIPT_EXECUTION=NO",
            f"FINAL_STATUS={final}",
            "",
        ]),
        encoding="utf-8",
    )


def read_sample(path: Path, size: int) -> str:
    if path.suffix.lower() not in TEXT_SAMPLE_EXTENSIONS:
        return ""

    if size > 16 * 1024 * 1024:
        return ""

    try:
        with path.open("rb") as handle:
            data = handle.read(131072)

        return data.decode(
            "utf-8",
            errors="ignore",
        ).lower()

    except OSError:
        return ""


def detect_sensitive(path_text: str, sample: str) -> bool:
    if any(signal in path_text for signal in STRONG_SENSITIVE_PATH_SIGNALS):
        return True

    strong_content = (
        "-----begin private key-----",
        "-----begin openssh private key-----",
        "-----begin rsa private key-----",
    )

    if any(signal in sample for signal in strong_content):
        return True

    for line in sample.splitlines():
        stripped = line.strip().lower()

        if re.match(
            r"^(password|passwd|api[_-]?key|secret|"
            r"access[_-]?token|refresh[_-]?token|"
            r"mnemonic|seed[_-]?phrase)\s*[:=]\s*\S+",
            stripped,
        ):
            return True

    return False


def classify(
    path: Path,
    sample: str,
) -> Tuple[List[str], List[str]]:
    name_lower = path.name.lower()
    path_lower = str(path).lower()
    suffix = path.suffix.lower()

    categories: List[str] = []
    proposals: List[str] = []

    if (
        suffix in SCRIPT_EXTENSIONS
        or name_lower in SCRIPT_NAMES
        or sample.startswith("#!")
    ):
        categories.append("SCRIPTS_RAW")

    if any(signal in path_lower for signal in DOCTRINE_SIGNALS):
        categories.append("DOCTRINES_README_SPECS")

    if (
        suffix in CONFIG_EXTENSIONS
        or name_lower in CONFIG_NAMES
        or name_lower.startswith(".env")
    ):
        categories.append("CONFIG_AND_DEPENDENCIES")

    if (
        suffix == ".log"
        or any(signal in path_lower for signal in TEST_SIGNALS)
    ):
        categories.append("TESTS_LOGS_AND_EXAMPLES")

    if suffix in DOCUMENT_EXTENSIONS:
        categories.append("DOCUMENTATION")

    lower_name = path.name.lower()

    if (
        suffix in ARCHIVE_EXTENSIONS
        or lower_name.endswith(".tar.gz")
        or lower_name.endswith(".tar.bz2")
        or lower_name.endswith(".tar.xz")
    ):
        categories.append("ARCHIVES_PENDING_REVIEW")

    for proposal_name, signals in TOPIC_PROPOSALS.items():
        if any(signal in path_lower for signal in signals):
            proposals.append(proposal_name)

    if not categories and (
        proposals
        or any(signal in path_lower for signal in HIGH_SIGNAL_TERMS)
    ):
        categories.append("REVIEW_REQUIRED")

    categories = list(dict.fromkeys(categories))
    proposals = list(dict.fromkeys(proposals))

    return categories, proposals


def embedded_origin(path: Path) -> str:
    value = str(path).lower()

    if "android" in value or "termux" in value:
        return "ANDROID_SIGNAL_ON_MAC"

    if "iphone" in value or "/ish" in value or "_ish" in value:
        return "IPHONE_ISH_SIGNAL_ON_MAC"

    if "lenovo" in value:
        return "LENOVO_SIGNAL_ON_MAC"

    if "msi" in value:
        return "MSI_SIGNAL_ON_MAC"

    if "asus" in value:
        return "ASUS_SIGNAL_ON_MAC"

    return "MAC_NATIVE_OR_UNRESOLVED"


def hash_file(path: Path, phase: str) -> str:
    digest = hashlib.sha256()
    last_update = time.monotonic()

    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)

            if not block:
                break

            digest.update(block)

            if time.monotonic() - last_update >= 2:
                write_status(
                    phase,
                    str(path),
                    "SHA256",
                    last_event=f"{phase}: {path.name}",
                )
                last_update = time.monotonic()

    return digest.hexdigest()


def copy_and_verify(
    source: Path,
    object_path: Path,
    expected_hash: str,
    size: int,
) -> bool:
    global hash_mismatches
    global copy_errors
    global copied_verified
    global copied_bytes
    global unique_objects

    free_bytes = shutil.disk_usage(MOUNT).free
    safety_margin = 10 * 1024**3

    if free_bytes < size + safety_margin:
        copy_errors += 1

        with ERROR_REPORT.open("a", encoding="utf-8") as handle:
            handle.write(
                f"LOW_SPACE\t{sanitize(source)}\t"
                f"SIZE={size}\tFREE={free_bytes}\n"
            )

        append_event(
            "LOW_SPACE_BLOCK",
            f"{source} size={size} free={free_bytes}",
        )

        return False

    object_path.parent.mkdir(parents=True, exist_ok=True)

    temp = object_path.with_name(
        f".{object_path.name}.{RUN_ID}.tmp"
    )

    try:
        with source.open("rb") as source_handle, temp.open("xb") as dest_handle:
            last_update = time.monotonic()

            while True:
                block = source_handle.read(8 * 1024 * 1024)

                if not block:
                    break

                dest_handle.write(block)

                if time.monotonic() - last_update >= 2:
                    write_status(
                        "COPYING",
                        str(source),
                        "UNIQUE_SHA256_OBJECT",
                        last_event=f"COPYING: {source.name}",
                    )
                    last_update = time.monotonic()

            dest_handle.flush()
            os.fsync(dest_handle.fileno())

        destination_hash = hash_file(
            temp,
            "VERIFYING_DESTINATION_SHA256",
        )

        if destination_hash != expected_hash:
            hash_mismatches += 1
            temp.unlink(missing_ok=True)

            with ERROR_REPORT.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"HASH_MISMATCH\t{sanitize(source)}\t"
                    f"SOURCE_SHA256={expected_hash}\t"
                    f"DEST_SHA256={destination_hash}\n"
                )

            return False

        os.replace(temp, object_path)

        copied_verified += 1
        copied_bytes += size
        unique_objects += 1

        return True

    except Exception as error:
        copy_errors += 1

        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass

        with ERROR_REPORT.open("a", encoding="utf-8") as handle:
            handle.write(
                f"COPY_ERROR\t{sanitize(source)}\t"
                f"{type(error).__name__}: {sanitize(error)}\n"
            )

        return False


def verify_existing_object(
    object_path: Path,
    expected_hash: str,
) -> bool:
    global hash_mismatches
    global copy_errors

    if expected_hash in validated_existing_objects:
        return True

    try:
        existing_hash = hash_file(
            object_path,
            "VERIFYING_EXISTING_UNIQUE_OBJECT",
        )

    except Exception as error:
        copy_errors += 1

        with ERROR_REPORT.open("a", encoding="utf-8") as handle:
            handle.write(
                f"EXISTING_OBJECT_READ_ERROR\t"
                f"{sanitize(object_path)}\t"
                f"{type(error).__name__}: {sanitize(error)}\n"
            )

        return False

    if existing_hash != expected_hash:
        hash_mismatches += 1

        with ERROR_REPORT.open("a", encoding="utf-8") as handle:
            handle.write(
                f"EXISTING_OBJECT_HASH_MISMATCH\t"
                f"{sanitize(object_path)}\t"
                f"EXPECTED={expected_hash}\t"
                f"ACTUAL={existing_hash}\n"
            )

        return False

    validated_existing_objects.add(expected_hash)
    return True


def should_skip_directory(parent: Path, name: str) -> bool:
    if name in SKIP_DIRECTORY_NAMES:
        return True

    if any(name.endswith(suffix) for suffix in SKIP_DIRECTORY_SUFFIXES):
        return True

    candidate = parent / name

    try:
        candidate_resolved = candidate.resolve()
        mount_resolved = MOUNT.resolve()

        if candidate_resolved == mount_resolved:
            return True

    except OSError:
        pass

    return False


def token_set(path: Path) -> Set[str]:
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        path.stem.lower(),
    )

    return {
        token
        for token in text.split()
        if len(token) >= 4
        and token not in {
            "script", "scripts", "doctrine",
            "doktrina", "readme", "final",
            "copy", "package", "system",
        }
    }


base_status = parse_status()
previous_mac_state = base_status.get("MAC_STATE", "UNKNOWN")

SOURCE_REGISTER.write_text(
    "SOURCE_DEVICE\tEMBEDDED_ORIGIN\tSOURCE_PATH\t"
    "SIZE_BYTES\tMTIME_NS\tSHA256\tCATEGORIES\t"
    "TOPIC_PROPOSALS\tACTION\n",
    encoding="utf-8",
)

DEVICE_SHA_MANIFEST.write_text(
    "SHA256\tSIZE_BYTES\tSOURCE_PATH\t"
    "OBJECT_PATH\tCOPY_STATUS\tCATEGORIES\n",
    encoding="utf-8",
)

GLOBAL_SHA_MANIFEST.write_text(
    "TIMESTAMP\tSOURCE_DEVICE\tEMBEDDED_ORIGIN\t"
    "SHA256\tSIZE_BYTES\tSOURCE_PATH\t"
    "OBJECT_PATH\tCOPY_STATUS\tCATEGORIES\n",
    encoding="utf-8",
)

DEVICE_DUPLICATE_MAP.write_text(
    "SHA256\tSOURCE_PATH\tFIRST_KNOWN_PATH\tOBJECT_PATH\n",
    encoding="utf-8",
)

GLOBAL_DUPLICATE_MAP.write_text(
    "SOURCE_DEVICE\tSHA256\tSOURCE_PATH\t"
    "FIRST_KNOWN_PATH\tOBJECT_PATH\n",
    encoding="utf-8",
)

SENSITIVE_REGISTER.write_text(
    "SOURCE_DEVICE\tSOURCE_PATH\tSIZE_BYTES\t"
    "MTIME_NS\tSHA256\tACTION\n",
    encoding="utf-8",
)

ERROR_REPORT.write_text(
    "ERROR_TYPE\tPATH\tDETAIL\n",
    encoding="utf-8",
)

LINK_REPORT.write_text(
    "SCRIPT_SHA256\tSCRIPT_PATH\tDOCTRINE_SHA256\t"
    "DOCTRINE_PATH\tLINK_TYPE\tSCORE\n",
    encoding="utf-8",
)

PROPOSAL_REPORT.write_text(
    "PROPOSAL_ID\tDEVICE_ID\tSUGGESTED_CATEGORY_NAME\t"
    "FILES_FOUND\tSAMPLE_SOURCE_PATH\tCONFIDENCE\t"
    "DECISION_STATUS\n",
    encoding="utf-8",
)

category_manifest_paths: Dict[str, Path] = {}

for category, directory in CATEGORY_PATHS.items():
    manifest = directory / f"MAC_{category}_{RUN_ID}.tsv"
    manifest.write_text(
        "SHA256\tSIZE_BYTES\tSOURCE_PATH\t"
        "OBJECT_PATH\tEMBEDDED_ORIGIN\tTOPIC_TAGS\n",
        encoding="utf-8",
    )
    category_manifest_paths[category] = manifest

SCOPE_REPORT.write_text(
    "\n".join([
        "============================================================",
        "MAC INGEST SOURCE SCOPE",
        "============================================================",
        f"HUMAN_GATE={HUMAN_GATE}",
        f"PROTOKOL={PROTOKOL}",
        f"RUN_ID={RUN_ID}",
        f"SOURCE_ROOT={HOME}",
        "MODE=HIGH_SIGNAL_TECHNICAL_AND_SSOT_DISCOVERY",
        "SYSTEM_LIBRARY_SCAN=NO",
        "APPLICATION_BUNDLE_SCAN=NO",
        "MEDIA_LIBRARY_SCAN=NO",
        "CACHE_SCAN=NO",
        "FOLLOW_SYMBOLIC_LINKS=NO",
        "ARCHIVE_EXTRACTION=NO",
        "SENSITIVE_CONTENT_COPY=NO_METADATA_ONLY",
        "SOURCE_DELETE=NO",
        "",
    ]),
    encoding="utf-8",
)

write_worker_status("RUNNING")
write_status(
    "INITIALIZING",
    str(HOME),
    "NONE",
    last_event="01_MAC INGEST STARTED",
)
append_event(
    "MAC_INGEST_STARTED",
    f"RUN_ID={RUN_ID} SOURCE_ROOT={HOME}",
)

print("============================================================")
print("FREYA 01_MAC INGEST — RUNNING")
print("============================================================")
print(f"RUN_ID={RUN_ID}")
print(f"SOURCE_ROOT={HOME}")
print(f"FACTORY={FACTORY}")
print(f"LIVE_STATUS={STATUS_FILE}")
print("SECOND_TERMINAL_MONITOR=ACTIVE")
print("SOURCE_DELETE=NO")
print()

fatal_error: Optional[str] = None

try:
    for directory, directory_names, file_names in os.walk(
        HOME,
        topdown=True,
        followlinks=False,
    ):
        current_directory = Path(directory)
        directories_examined += 1

        kept_directories = []

        for name in directory_names:
            if should_skip_directory(current_directory, name):
                continue

            kept_directories.append(name)

        directory_names[:] = kept_directories

        for file_name in file_names:
            files_examined += 1
            source = current_directory / file_name

            try:
                if source.is_symlink() or not source.is_file():
                    continue

                stat = source.stat()

            except OSError as error:
                scan_errors += 1

                with ERROR_REPORT.open("a", encoding="utf-8") as handle:
                    handle.write(
                        f"STAT_ERROR\t{sanitize(source)}\t"
                        f"{type(error).__name__}: {sanitize(error)}\n"
                    )

                continue

            sample = read_sample(source, stat.st_size)
            categories, proposals = classify(source, sample)

            if not categories:
                low_signal_skipped += 1
                continue

            valuable_discovered += 1
            discovered_bytes += stat.st_size

            category_text = ",".join(categories)

            write_status(
                "DISCOVERY_AND_CLASSIFICATION",
                str(source),
                category_text,
                last_event=f"DISCOVERED: {source.name}",
            )

            source_path_lower = str(source).lower()
            sensitive = detect_sensitive(
                source_path_lower,
                sample,
            )

            try:
                source_hash = hash_file(
                    source,
                    "HASHING_SOURCE_SHA256",
                )

            except Exception as error:
                copy_errors += 1

                with ERROR_REPORT.open("a", encoding="utf-8") as handle:
                    handle.write(
                        f"SOURCE_HASH_ERROR\t{sanitize(source)}\t"
                        f"{type(error).__name__}: {sanitize(error)}\n"
                    )

                continue

            origin = embedded_origin(source)

            with SOURCE_REGISTER.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"01_MAC\t{origin}\t"
                    f"{sanitize(source)}\t"
                    f"{stat.st_size}\t"
                    f"{stat.st_mtime_ns}\t"
                    f"{source_hash}\t"
                    f"{category_text}\t"
                    f"{','.join(proposals)}\t"
                    f"{'METADATA_ONLY_SENSITIVE' if sensitive else 'COPY_OR_DEDUPE'}\n"
                )

            for proposal in proposals:
                entry = proposal_hits.setdefault(
                    proposal,
                    {
                        "count": 0,
                        "sample": str(source),
                    },
                )
                entry["count"] = int(entry["count"]) + 1

            if sensitive:
                sensitive_required += 1

                with SENSITIVE_REGISTER.open(
                    "a",
                    encoding="utf-8",
                ) as handle:
                    handle.write(
                        f"01_MAC\t{sanitize(source)}\t"
                        f"{stat.st_size}\t"
                        f"{stat.st_mtime_ns}\t"
                        f"{source_hash}\t"
                        "METADATA_ONLY_HUMAN_GATE_REQUIRED\n"
                    )

                write_status(
                    "SENSITIVE_METADATA_ONLY",
                    str(source),
                    "SENSITIVE_REVIEW_REQUIRED",
                    last_arrival=str(source),
                    last_event=f"SENSITIVE HOLD: {source.name}",
                )

                continue

            object_path = (
                UNIQUE_ROOT
                / source_hash[:2]
                / source_hash
            )

            duplicate = False
            copy_status = "UNKNOWN"

            if object_path.exists():
                if verify_existing_object(
                    object_path,
                    source_hash,
                ):
                    duplicate = True
                    copy_status = "EXISTING_OBJECT_SHA256_VERIFIED"
                else:
                    copy_status = "EXISTING_OBJECT_VERIFICATION_FAILED"

            else:
                if copy_and_verify(
                    source,
                    object_path,
                    source_hash,
                    stat.st_size,
                ):
                    validated_existing_objects.add(source_hash)
                    copy_status = "NEW_OBJECT_COPIED_SHA256_VERIFIED"
                else:
                    copy_status = "COPY_OR_VERIFICATION_FAILED"

            first_known = seen_hash_paths.get(source_hash)

            if first_known is None:
                seen_hash_paths[source_hash] = str(source)

            elif first_known != str(source):
                duplicate = True

            if duplicate:
                duplicate_paths += 1
                first_path = (
                    first_known
                    or "EXISTING_FROM_PREVIOUS_INGEST"
                )

                row = (
                    f"{source_hash}\t"
                    f"{sanitize(source)}\t"
                    f"{sanitize(first_path)}\t"
                    f"{sanitize(object_path)}\n"
                )

                with DEVICE_DUPLICATE_MAP.open(
                    "a",
                    encoding="utf-8",
                ) as handle:
                    handle.write(row)

                with GLOBAL_DUPLICATE_MAP.open(
                    "a",
                    encoding="utf-8",
                ) as handle:
                    handle.write(
                        f"01_MAC\t{row}"
                    )

            lineage_row = (
                f"{source_hash}\t"
                f"{stat.st_size}\t"
                f"{sanitize(source)}\t"
                f"{sanitize(object_path)}\t"
                f"{copy_status}\t"
                f"{category_text}\n"
            )

            with DEVICE_SHA_MANIFEST.open(
                "a",
                encoding="utf-8",
            ) as handle:
                handle.write(lineage_row)

            with GLOBAL_SHA_MANIFEST.open(
                "a",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    f"{datetime.now().isoformat(timespec='seconds')}\t"
                    f"01_MAC\t{origin}\t"
                    f"{lineage_row}"
                )

            topic_text = ",".join(proposals)

            for category in categories:
                manifest = category_manifest_paths[category]

                with manifest.open(
                    "a",
                    encoding="utf-8",
                ) as handle:
                    handle.write(
                        f"{source_hash}\t"
                        f"{stat.st_size}\t"
                        f"{sanitize(source)}\t"
                        f"{sanitize(object_path)}\t"
                        f"{origin}\t"
                        f"{topic_text}\n"
                    )

            if "SCRIPTS_RAW" in categories:
                scripts_classified += 1
                scripts.append((source, source_hash))

            if "DOCTRINES_README_SPECS" in categories:
                doctrines_classified += 1
                doctrines.append((source, source_hash))

            if "CONFIG_AND_DEPENDENCIES" in categories:
                configs_classified += 1

            if "TESTS_LOGS_AND_EXAMPLES" in categories:
                tests_classified += 1

            if "DOCUMENTATION" in categories:
                documentation_classified += 1

            if "ARCHIVES_PENDING_REVIEW" in categories:
                archives_held += 1

            if "REVIEW_REQUIRED" in categories:
                review_required += 1

            write_status(
                "INGESTED_AND_REGISTERED",
                str(source),
                category_text,
                last_arrival=str(source),
                last_event=(
                    f"{copy_status}: {source.name}"
                ),
            )

            if valuable_discovered % 25 == 0:
                print(
                    "MAC_PROGRESS "
                    f"DISCOVERED={valuable_discovered} "
                    f"COPIED_VERIFIED={copied_verified} "
                    f"UNIQUE={unique_objects} "
                    f"DUPLICATES={duplicate_paths} "
                    f"SENSITIVE={sensitive_required} "
                    f"ERRORS={copy_errors} "
                    f"HASH_MISMATCHES={hash_mismatches}"
                )

                append_event(
                    "MAC_PROGRESS",
                    (
                        f"discovered={valuable_discovered} "
                        f"copied={copied_verified} "
                        f"unique={unique_objects} "
                        f"duplicates={duplicate_paths}"
                    ),
                )

except KeyboardInterrupt:
    fatal_error = "HUMAN_INTERRUPTION_CTRL_C"
    append_event(
        "MAC_INGEST_INTERRUPTED",
        fatal_error,
    )

except Exception as error:
    fatal_error = (
        f"{type(error).__name__}: {sanitize(error)}"
    )

    with ERROR_REPORT.open("a", encoding="utf-8") as handle:
        handle.write(
            f"FATAL_ERROR\tMAC_INGEST\t{fatal_error}\n"
        )

    append_event(
        "MAC_INGEST_FATAL_ERROR",
        fatal_error,
    )

write_status(
    "BUILDING_SCRIPT_DOCTRINE_LINKS",
    "NONE",
    "SCRIPT_DOCTRINE_LINKS",
    last_event="BUILDING STATIC SCRIPT DOCTRINE LINKS",
)

doctrines_by_directory: Dict[str, List[Tuple[Path, str]]] = defaultdict(list)

for doctrine_path, doctrine_hash in doctrines:
    doctrines_by_directory[str(doctrine_path.parent)].append(
        (doctrine_path, doctrine_hash)
    )

    doctrines_by_directory[str(doctrine_path.parent.parent)].append(
        (doctrine_path, doctrine_hash)
    )

with LINK_REPORT.open("a", encoding="utf-8") as link_handle:
    for script_path, script_hash in scripts:
        candidates: List[Tuple[int, Path, str]] = []
        script_tokens = token_set(script_path)

        possible = (
            doctrines_by_directory.get(
                str(script_path.parent),
                [],
            )
            + doctrines_by_directory.get(
                str(script_path.parent.parent),
                [],
            )
        )

        seen_docs: Set[str] = set()

        for doctrine_path, doctrine_hash in possible:
            if doctrine_hash in seen_docs:
                continue

            seen_docs.add(doctrine_hash)

            doctrine_tokens = token_set(doctrine_path)
            score = len(
                script_tokens.intersection(doctrine_tokens)
            )

            if doctrine_path.parent == script_path.parent:
                score += 3
            else:
                score += 1

            candidates.append(
                (
                    score,
                    doctrine_path,
                    doctrine_hash,
                )
            )

        for score, doctrine_path, doctrine_hash in sorted(
            candidates,
            key=lambda item: (
                -item[0],
                str(item[1]).casefold(),
            ),
        )[:3]:
            link_handle.write(
                f"{script_hash}\t"
                f"{sanitize(script_path)}\t"
                f"{doctrine_hash}\t"
                f"{sanitize(doctrine_path)}\t"
                "CANDIDATE_STATIC_PROXIMITY_LINK\t"
                f"{score}\n"
            )

            script_doctrine_links += 1

for index, proposal_name in enumerate(
    sorted(proposal_hits),
    start=1,
):
    proposal = proposal_hits[proposal_name]
    count = int(proposal["count"])
    confidence = (
        "HIGH"
        if count >= 20
        else "MEDIUM"
        if count >= 5
        else "LOW"
    )

    with PROPOSAL_REPORT.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            f"MAC_CAT_{index:04d}\t"
            f"01_MAC\t"
            f"{proposal_name}\t"
            f"{count}\t"
            f"{sanitize(proposal['sample'])}\t"
            f"{confidence}\t"
            "HUMAN_GATE_PENDING\n"
        )

DEVICE_PROPOSAL_POINTER.write_text(
    "\n".join([
        f"DEVICE=01_MAC",
        f"RUN_ID={RUN_ID}",
        f"GLOBAL_PROPOSAL_FILE={PROPOSAL_REPORT}",
        f"PROPOSAL_COUNT={len(proposal_hits)}",
        "HUMAN_GATE_DECISION=REQUIRED",
        "",
    ]),
    encoding="utf-8",
)

completed_at = datetime.now().isoformat(timespec="seconds")
elapsed_seconds = int(time.monotonic() - start_monotonic)
free_gib = shutil.disk_usage(MOUNT).free / 1024**3

clean_completion = (
    fatal_error is None
    and hash_mismatches == 0
    and copy_errors == 0
)

if clean_completion:
    final_status = (
        "MAC_ACCESSIBLE_HIGH_SIGNAL_SCOPE_INGESTED_AND_VERIFIED"
    )
    final_mac_state = "ACCESSIBLE_SCOPE_HOME_VERIFIED"

    home_count = int_status("DEVICES_HOME_VERIFIED")

    if previous_mac_state != "ACCESSIBLE_SCOPE_HOME_VERIFIED":
        base_status["DEVICES_HOME_VERIFIED"] = str(home_count + 1)

else:
    final_status = (
        "MAC_INGEST_COMPLETED_WITH_REVIEW_REQUIRED"
        if fatal_error is None
        else "MAC_INGEST_INTERRUPTED_REVIEW_REQUIRED"
    )
    final_mac_state = "REVIEW_REQUIRED"

base_status["MAC_STATE"] = final_mac_state

write_status(
    "COMPLETED" if fatal_error is None else "INTERRUPTED",
    "NONE",
    "NONE",
    last_event=final_status,
    final_status=final_status,
)

summary_lines = [
    "============================================================",
    "FREYA 01_MAC INGEST — FINAL SUMMARY",
    "============================================================",
    f"HUMAN_GATE={HUMAN_GATE}",
    f"PROTOKOL={PROTOKOL}",
    f"RUN_ID={RUN_ID}",
    f"STARTED_AT={started_at}",
    f"COMPLETED_AT={completed_at}",
    f"ELAPSED_SECONDS={elapsed_seconds}",
    f"SOURCE_ROOT={HOME}",
    "",
    f"DIRECTORIES_EXAMINED={directories_examined}",
    f"FILES_EXAMINED={files_examined}",
    f"LOW_SIGNAL_FILES_SKIPPED={low_signal_skipped}",
    f"SOURCE_FILES_DISCOVERED={valuable_discovered}",
    f"SOURCE_BYTES_DISCOVERED={discovered_bytes}",
    f"FILES_COPIED_VERIFIED={copied_verified}",
    f"BYTES_COPIED_VERIFIED={copied_bytes}",
    f"UNIQUE_SHA256_OBJECTS={unique_objects}",
    f"DUPLICATE_PATHS_MAPPED={duplicate_paths}",
    f"SCRIPTS_CLASSIFIED={scripts_classified}",
    f"DOCTRINES_CLASSIFIED={doctrines_classified}",
    f"CONFIGS_CLASSIFIED={configs_classified}",
    f"TESTS_LOGS_EXAMPLES_CLASSIFIED={tests_classified}",
    f"DOCUMENTATION_CLASSIFIED={documentation_classified}",
    f"ARCHIVES_HELD={archives_held}",
    f"SCRIPT_DOCTRINE_LINKS={script_doctrine_links}",
    f"NEW_CATEGORY_PROPOSALS={len(proposal_hits)}",
    f"REVIEW_REQUIRED={review_required}",
    f"SENSITIVE_METADATA_ONLY={sensitive_required}",
    f"SCAN_ERRORS={scan_errors}",
    f"COPY_ERRORS={copy_errors}",
    f"HASH_MISMATCHES={hash_mismatches}",
    f"FREE_GIB_AFTER={free_gib:.3f}",
    f"FATAL_ERROR={fatal_error or 'NONE'}",
    "",
    "SOURCE_FILES_DELETED=0",
    "SOURCE_FILES_MOVED=0",
    "SOURCE_FILES_RENAMED=0",
    "DISCOVERED_SCRIPTS_EXECUTED=0",
    "ARCHIVES_EXTRACTED=0",
    f"FINAL_STATUS={final_status}",
    "============================================================",
    "",
]

SUMMARY_REPORT.write_text(
    "\n".join(summary_lines),
    encoding="utf-8",
)

GAP_REPORT.write_text(
    "\n".join([
        "============================================================",
        "MAC DEVICE GAP REGISTER",
        "============================================================",
        f"RUN_ID={RUN_ID}",
        "COMPLETED_SCOPE=USER_HOME_HIGH_SIGNAL_TECHNICAL_AND_SSOT",
        "EXCLUDED_SCOPE=MACOS_LIBRARY_APPLICATIONS_MEDIA_AND_CACHES",
        "SYSTEM_LIBRARY_DEEP_SCAN=NOT_PERFORMED",
        "APPLICATION_DATABASE_EXTRACTION=NOT_PERFORMED",
        "MEDIA_LIBRARY_INGEST=NOT_PERFORMED",
        "SENSITIVE_CONTENT=METADATA_ONLY_HUMAN_GATE_REQUIRED",
        f"SCAN_ERRORS={scan_errors}",
        f"COPY_ERRORS={copy_errors}",
        f"HASH_MISMATCHES={hash_mismatches}",
        f"NEXT_DEVICE=02_ANDROID",
        "============================================================",
        "",
    ]),
    encoding="utf-8",
)

receipt_content = "\n".join([
    "============================================================",
    "MAC INGEST RECEIPT",
    "============================================================",
    f"HUMAN_GATE={HUMAN_GATE}",
    f"PROTOKOL={PROTOKOL}",
    f"RUN_ID={RUN_ID}",
    f"SOURCE_DEVICE=01_MAC",
    f"SOURCE_FILES_DISCOVERED={valuable_discovered}",
    f"FILES_COPIED_VERIFIED={copied_verified}",
    f"UNIQUE_SHA256_OBJECTS={unique_objects}",
    f"DUPLICATE_PATHS_MAPPED={duplicate_paths}",
    f"HASH_MISMATCHES={hash_mismatches}",
    f"COPY_ERRORS={copy_errors}",
    "SOURCE_FILES_DELETED=0",
    f"SUMMARY_REPORT={SUMMARY_REPORT}",
    f"SOURCE_REGISTER={SOURCE_REGISTER}",
    f"SHA256_MANIFEST={GLOBAL_SHA_MANIFEST}",
    f"DUPLICATE_MAP={GLOBAL_DUPLICATE_MAP}",
    f"SCRIPT_DOCTRINE_LINKS={LINK_REPORT}",
    f"CATEGORY_PROPOSALS={PROPOSAL_REPORT}",
    f"FINAL_STATUS={final_status}",
    "============================================================",
    "",
])

RECEIPT.write_text(
    receipt_content,
    encoding="utf-8",
)

receipt_hash = hashlib.sha256(
    RECEIPT.read_bytes()
).hexdigest()

(RECEIPT.with_suffix(".txt.sha256")).write_text(
    f"{receipt_hash}  {RECEIPT.name}\n",
    encoding="utf-8",
)

write_worker_status(
    "COMPLETED" if fatal_error is None else "INTERRUPTED",
    final_status,
)

append_event(
    "MAC_INGEST_FINISHED",
    (
        f"status={final_status} "
        f"discovered={valuable_discovered} "
        f"copied={copied_verified} "
        f"unique={unique_objects} "
        f"duplicates={duplicate_paths} "
        f"errors={copy_errors} "
        f"mismatches={hash_mismatches}"
    ),
)

try:
    LOCK_DIR.rmdir()
except OSError:
    pass

print()
print("============================================================")
print("FREYA 01_MAC INGEST — FINAL")
print("============================================================")
print(f"DIRECTORIES_EXAMINED={directories_examined}")
print(f"FILES_EXAMINED={files_examined}")
print(f"SOURCE_FILES_DISCOVERED={valuable_discovered}")
print(f"FILES_COPIED_VERIFIED={copied_verified}")
print(f"UNIQUE_SHA256_OBJECTS={unique_objects}")
print(f"DUPLICATE_PATHS_MAPPED={duplicate_paths}")
print(f"SCRIPTS_CLASSIFIED={scripts_classified}")
print(f"DOCTRINES_CLASSIFIED={doctrines_classified}")
print(f"CONFIGS_CLASSIFIED={configs_classified}")
print(f"DOCUMENTATION_CLASSIFIED={documentation_classified}")
print(f"ARCHIVES_HELD={archives_held}")
print(f"SCRIPT_DOCTRINE_LINKS={script_doctrine_links}")
print(f"NEW_CATEGORY_PROPOSALS={len(proposal_hits)}")
print(f"SENSITIVE_METADATA_ONLY={sensitive_required}")
print(f"SCAN_ERRORS={scan_errors}")
print(f"COPY_ERRORS={copy_errors}")
print(f"HASH_MISMATCHES={hash_mismatches}")
print("SOURCE_FILES_DELETED=0")
print(f"FREE_GIB_AFTER={free_gib:.3f}")
print(f"SUMMARY_REPORT={SUMMARY_REPORT}")
print(f"RECEIPT={RECEIPT}")
print(f"RECEIPT_SHA256={receipt_hash}")
print(f"FINAL_STATUS={final_status}")
print("NEXT_SAFE_ACTION=RETURN_COMPLETE_TERMINAL_OUTPUT")
print("============================================================")

if fatal_error is not None:
    raise SystemExit(30)

if copy_errors or hash_mismatches:
    raise SystemExit(31)
