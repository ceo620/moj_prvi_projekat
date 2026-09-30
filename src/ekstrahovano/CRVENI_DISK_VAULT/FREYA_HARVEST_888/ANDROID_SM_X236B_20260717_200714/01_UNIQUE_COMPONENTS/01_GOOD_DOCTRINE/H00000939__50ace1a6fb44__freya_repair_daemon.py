import csv
import errno
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import sys
import time
import traceback
from collections import Counter
from datetime import datetime

PLAN = pathlib.Path(os.environ["FREYA_PLAN"])
BASE = pathlib.Path(os.environ["FREYA_BASE"])
STOP_AT = int(os.environ["FREYA_STOP_AT_EPOCH"])
EXT_ROOT = pathlib.Path(os.environ["FREYA_EXT_ROOT"])

FILES_DIR = BASE / "01_REPAIRED_COPIES"
REPORTS_DIR = BASE / "02_REPORTS"
HOLD_DIR = BASE / "03_HOLD_INCOMPLETE"
CONTROL_DIR = BASE / "04_CONTROL"

for directory in (
    FILES_DIR,
    REPORTS_DIR,
    HOLD_DIR,
    CONTROL_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)

STATUS = CONTROL_DIR / "STATUS.txt"
LOCK = pathlib.Path.home() / ".freya_repair_daemon.pidlock"
PIDFILE = CONTROL_DIR / "daemon.pid"

DB_PATH = REPORTS_DIR / "STATE.sqlite3"
MANIFEST = REPORTS_DIR / "REPAIRED_MANIFEST.psv"
ERRORS = REPORTS_DIR / "ERROR_LEDGER.psv"
LEARNING = REPORTS_DIR / "LEARNING_LEDGER.json"
SUMMARY = REPORTS_DIR / "FINAL_SUMMARY.txt"

MIN_FREE_BYTES = 10 * 1024**3
MAX_SINGLE_FILE = 1024 * 1024**3
RETRY_LIMIT = 3

SAFE_DOCUMENTS = {
    ".pdf", ".doc", ".docx",
    ".xls", ".xlsx", ".xlsm",
    ".csv", ".ppt", ".pptx",
    ".odt", ".ods", ".odp",
    ".rtf", ".txt", ".md",
    ".json", ".xml", ".html",
    ".htm", ".eml", ".msg",
}

MEDIA = {
    ".jpg", ".jpeg", ".png",
    ".gif", ".bmp", ".tif",
    ".tiff", ".webp", ".heic",
    ".mp3", ".wav", ".m4a",
    ".mp4", ".mov", ".avi",
    ".mkv",
}

SCRIPTS = {
    ".sh", ".bash", ".zsh",
    ".py", ".pyc", ".ps1",
    ".bat", ".cmd", ".js",
    ".ts", ".php", ".pl",
    ".rb", ".jar", ".apk",
}

BINARIES = {
    ".exe", ".dll", ".so",
    ".dylib", ".bin", ".msi",
    ".deb", ".rpm",
}

ARCHIVES = {
    ".zip", ".tar", ".gz",
    ".tgz", ".bz2", ".xz",
    ".7z", ".rar",
}

SENSITIVE_TERMS = (
    "seed phrase",
    "seed_phrase",
    "mnemonic",
    "private key",
    "private_key",
    "recovery phrase",
    "recovery_phrase",
    "keystore",
    "wallet.dat",
    "id_rsa",
    "secret_key",
)


def now():
    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def psv(value):
    return (
        str(value)
        .replace("|", "/")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def atomic_write(path, text):
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        text,
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_status(
    state,
    counters,
    current="",
    note="",
):
    free_bytes = shutil.disk_usage(
        EXT_ROOT
    ).free

    status_text = "\n".join(
        [
            "FREYA_REPAIR_DAEMON_STATUS",
            f"UPDATED={now()}",
            f"STATE={state}",
            f"PID={os.getpid()}",
            f"PLAN={PLAN}",
            f"BASE={BASE}",
            f"STOP_AT_EPOCH={STOP_AT}",
            (
                "STOP_AT_LOCAL="
                + datetime.fromtimestamp(
                    STOP_AT
                ).astimezone().isoformat(
                    timespec="seconds"
                )
            ),
            f"CURRENT_SOURCE={current}",
            (
                "SCANNED="
                f"{counters.get('SCANNED', 0)}"
            ),
            (
                "COPIED_VERIFIED="
                f"{counters.get('COPIED_VERIFIED', 0)}"
            ),
            (
                "DUPLICATE_HASH_SKIPPED="
                f"{counters.get('DUPLICATE_HASH_SKIPPED', 0)}"
            ),
            f"HOLD={counters.get('HOLD', 0)}",
            f"ERRORS={counters.get('ERRORS', 0)}",
            (
                "EXTERNAL_FREE_GIB="
                f"{free_bytes / 1024**3:.3f}"
            ),
            f"NOTE={note}",
            "HUMAN_GATE=ACTIVE",
            (
                "APPROVAL="
                "EXPLICIT_DANIJELA_20260712"
            ),
            "ORIGINALS_CHANGED=NO",
            "ORIGINALS_MOVED=NO",
            "ORIGINALS_RENAMED=NO",
            "FILES_DELETED=NO",
            "ARCHIVES_OPENED=NO",
            "SCRIPTS_EXECUTED=NO",
            (
                "DAEMONS_STARTED="
                "YES_ONE_CONTROLLED_REPAIR_DAEMON"
            ),
            "INTERNET_USED=NO",
            "",
        ]
    )

    atomic_write(
        STATUS,
        status_text,
    )


def classify(path):
    lower_name = path.name.lower()
    extension = path.suffix.lower()

    if (
        any(
            term in lower_name
            for term in SENSITIVE_TERMS
        )
        or extension
        in {".pem", ".key", ".p12", ".pfx"}
    ):
        return (
            "SENSITIVE_HOLD",
            ".SENSITIVE_HOLD",
        )

    if extension in SAFE_DOCUMENTS:
        return (
            "DOCUMENTS",
            extension or ".dat",
        )

    if extension in MEDIA:
        return (
            "MEDIA",
            extension or ".dat",
        )

    if extension in SCRIPTS:
        return (
            "SCRIPTS_DO_NOT_RUN",
            (extension or ".dat")
            + ".DO_NOT_RUN",
        )

    if extension in BINARIES:
        return (
            "BINARIES_HOLD",
            (extension or ".dat")
            + ".BINARY_HOLD",
        )

    if extension in ARCHIVES:
        return (
            "ARCHIVES_HOLD",
            (extension or ".dat")
            + ".ARCHIVE_HOLD",
        )

    if 0 < len(extension) <= 12:
        suffix = extension
    else:
        suffix = ".dat"

    return (
        "OTHER_FILES",
        suffix,
    )


def error_code(exception):
    if isinstance(
        exception,
        PermissionError,
    ):
        return "PERMISSION_DENIED"

    if isinstance(
        exception,
        FileNotFoundError,
    ):
        return "SOURCE_NOT_FOUND"

    if isinstance(
        exception,
        OSError,
    ):
        if exception.errno == errno.ENAMETOOLONG:
            return "FILE_NAME_TOO_LONG"

        if exception.errno == errno.ENOSPC:
            return "NO_SPACE_LEFT"

        if exception.errno == errno.EIO:
            return "IO_ERROR"

        if exception.errno == errno.EROFS:
            return "READ_ONLY_FILESYSTEM"

    return type(exception).__name__.upper()


def acquire_lock():
    while True:
        try:
            descriptor = os.open(
                LOCK,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY,
                0o600,
            )

            os.write(
                descriptor,
                str(os.getpid()).encode("ascii"),
            )

            return descriptor

        except FileExistsError:
            try:
                old_pid = int(
                    LOCK.read_text(
                        encoding="utf-8",
                        errors="replace",
                    ).strip()
                )
            except Exception:
                old_pid = -1

            if old_pid > 0:
                try:
                    os.kill(old_pid, 0)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    print(
                        "FINAL_STATUS="
                        "BLOCKED_LOCK_PID_PERMISSION"
                    )
                    sys.exit(2)
                else:
                    print(
                        "FINAL_STATUS="
                        "BLOCKED_ANOTHER_REPAIR_"
                        "DAEMON_IS_RUNNING"
                    )
                    sys.exit(2)

            try:
                LOCK.unlink()
            except FileNotFoundError:
                continue
            except OSError as exception:
                print(
                    "FINAL_STATUS="
                    "BLOCKED_STALE_LOCK_"
                    + type(exception).__name__.upper()
                )
                sys.exit(2)


lock_fd = acquire_lock()


PIDFILE.write_text(
    str(os.getpid()),
    encoding="utf-8",
)

connection = sqlite3.connect(
    DB_PATH
)

connection.execute(
    "PRAGMA journal_mode=WAL"
)

connection.execute(
    """
    CREATE TABLE IF NOT EXISTS items(
        source TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        sha256 TEXT,
        destination TEXT,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        updated TEXT NOT NULL
    )
    """
)

connection.execute(
    """
    CREATE TABLE IF NOT EXISTS hashes(
        sha256 TEXT PRIMARY KEY,
        destination TEXT NOT NULL,
        updated TEXT NOT NULL
    )
    """
)

connection.commit()

if not MANIFEST.exists():
    MANIFEST.write_text(
        (
            "TIME|RECORD_ID|CATEGORY|CLASS|"
            "SIZE_BYTES|SHA256|SOURCE_PATH|"
            "DESTINATION_PATH|STATUS\n"
        ),
        encoding="utf-8",
    )

if not ERRORS.exists():
    ERRORS.write_text(
        (
            "TIME|RECORD_ID|ATTEMPT|"
            "ERROR_CODE|SOURCE_PATH|"
            "DETAIL|ACTION\n"
        ),
        encoding="utf-8",
    )

counters = Counter()
error_counts = Counter()

rules = {
    "FILE_NAME_TOO_LONG": (
        "Use short hash-based destination names."
    ),
    "DUPLICATE_HASH": (
        "Do not copy content already verified."
    ),
    "PERMISSION_DENIED": (
        "Retry with backoff; hold after "
        "three failures."
    ),
    "SOURCE_NOT_FOUND": (
        "Retry; hold after three failures."
    ),
    "NO_SPACE_LEFT": (
        "Stop cleanly before external disk "
        "becomes unsafe."
    ),
    "HASH_MISMATCH": (
        "Keep incomplete copy in HOLD and "
        "never replace verified output."
    ),
    "SENSITIVE_HOLD": (
        "Do not automatically copy likely "
        "credential or wallet material."
    ),
}

with PLAN.open(
    "r",
    encoding="utf-8",
    errors="replace",
    newline="",
) as plan_file:
    total_rows = sum(
        1 for _ in plan_file
    ) - 1

write_status(
    "RUNNING",
    counters,
    note=f"PLAN_ROWS={max(total_rows, 0)}",
)

try:
    with PLAN.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as plan_file:

        reader = csv.DictReader(
            plan_file,
            delimiter="|",
        )

        for row in reader:
            if time.time() >= STOP_AT:
                write_status(
                    "STOPPED_AT_DEADLINE",
                    counters,
                    note=(
                        "Deadline reached safely"
                    ),
                )
                break

            free_bytes = shutil.disk_usage(
                EXT_ROOT
            ).free

            if free_bytes < MIN_FREE_BYTES:
                error_counts[
                    "LOW_EXTERNAL_SPACE"
                ] += 1

                write_status(
                    "STOPPED_LOW_EXTERNAL_SPACE",
                    counters,
                    note=(
                        "External free space "
                        "below 10 GiB"
                    ),
                )
                break

            source_text = row.get(
                "SOURCE_PATH",
                "",
            )
            record_id = row.get(
                "RECORD_ID",
                "",
            )
            category = row.get(
                "CATEGORY",
                "",
            )

            source = pathlib.Path(
                source_text
            )

            counters["SCANNED"] += 1

            previous = connection.execute(
                (
                    "SELECT status "
                    "FROM items "
                    "WHERE source=?"
                ),
                (source_text,),
            ).fetchone()

            if (
                previous
                and previous[0]
                in {
                    "COPIED_VERIFIED",
                    "DUPLICATE_HASH_SKIPPED",
                    "SENSITIVE_HOLD",
                    "HOLD",
                }
            ):
                continue

            if counters["SCANNED"] % 25 == 0:
                write_status(
                    "RUNNING",
                    counters,
                    current=source_text,
                )

            if source.is_symlink():
                counters["HOLD"] += 1
                error_counts[
                    "SYMLINK_BLOCKED"
                ] += 1

                connection.execute(
                    (
                        "INSERT INTO items("
                        "source,status,attempts,"
                        "last_error,updated"
                        ") VALUES(?,?,?,?,?) "
                        "ON CONFLICT(source) "
                        "DO UPDATE SET "
                        "status=excluded.status,"
                        "last_error="
                        "excluded.last_error,"
                        "updated=excluded.updated"
                    ),
                    (
                        source_text,
                        "HOLD",
                        0,
                        "SYMLINK_BLOCKED",
                        now(),
                    ),
                )

                connection.commit()
                continue

            class_name, output_suffix = classify(
                source
            )

            if class_name == "SENSITIVE_HOLD":
                counters["HOLD"] += 1
                error_counts[
                    "SENSITIVE_HOLD"
                ] += 1

                connection.execute(
                    (
                        "INSERT INTO items("
                        "source,status,attempts,"
                        "last_error,updated"
                        ") VALUES(?,?,?,?,?) "
                        "ON CONFLICT(source) "
                        "DO UPDATE SET "
                        "status=excluded.status,"
                        "last_error="
                        "excluded.last_error,"
                        "updated=excluded.updated"
                    ),
                    (
                        source_text,
                        "SENSITIVE_HOLD",
                        0,
                        "SENSITIVE_NAME_MATCH",
                        now(),
                    ),
                )

                connection.commit()

                with ERRORS.open(
                    "a",
                    encoding="utf-8",
                ) as error_file:
                    error_file.write(
                        f"{now()}|"
                        f"{psv(record_id)}|"
                        "0|SENSITIVE_HOLD|"
                        f"{psv(source_text)}|"
                        "Filename matched "
                        "sensitive rule|"
                        "METADATA_ONLY_HOLD\n"
                    )

                continue

            success = False
            last_exception = None

            for attempt in range(
                1,
                RETRY_LIMIT + 1,
            ):
                try:
                    if not source.is_file():
                        raise FileNotFoundError(
                            source_text
                        )

                    source_size = (
                        source.stat().st_size
                    )

                    if (
                        source_size
                        > MAX_SINGLE_FILE
                    ):
                        counters["HOLD"] += 1
                        error_counts[
                            "FILE_TOO_LARGE"
                        ] += 1

                        connection.execute(
                            (
                                "INSERT INTO items("
                                "source,status,"
                                "attempts,last_error,"
                                "updated"
                                ") VALUES(?,?,?,?,?) "
                                "ON CONFLICT(source) "
                                "DO UPDATE SET "
                                "status=excluded.status,"
                                "attempts="
                                "excluded.attempts,"
                                "last_error="
                                "excluded.last_error,"
                                "updated="
                                "excluded.updated"
                            ),
                            (
                                source_text,
                                "HOLD",
                                attempt,
                                "FILE_TOO_LARGE",
                                now(),
                            ),
                        )

                        connection.commit()
                        success = True
                        break

                    source_hash = sha256_file(
                        source
                    )

                    existing = (
                        connection.execute(
                            (
                                "SELECT destination "
                                "FROM hashes "
                                "WHERE sha256=?"
                            ),
                            (source_hash,),
                        ).fetchone()
                    )

                    if existing:
                        counters[
                            "DUPLICATE_HASH_SKIPPED"
                        ] += 1

                        connection.execute(
                            (
                                "INSERT INTO items("
                                "source,status,sha256,"
                                "destination,attempts,"
                                "last_error,updated"
                                ") VALUES(?,?,?,?,?,?,?) "
                                "ON CONFLICT(source) "
                                "DO UPDATE SET "
                                "status=excluded.status,"
                                "sha256=excluded.sha256,"
                                "destination="
                                "excluded.destination,"
                                "attempts="
                                "excluded.attempts,"
                                "last_error=NULL,"
                                "updated="
                                "excluded.updated"
                            ),
                            (
                                source_text,
                                (
                                    "DUPLICATE_"
                                    "HASH_SKIPPED"
                                ),
                                source_hash,
                                existing[0],
                                attempt,
                                None,
                                now(),
                            ),
                        )

                        connection.commit()

                        with MANIFEST.open(
                            "a",
                            encoding="utf-8",
                        ) as manifest_file:
                            manifest_file.write(
                                f"{now()}|"
                                f"{psv(record_id)}|"
                                f"{psv(category)}|"
                                f"{class_name}|"
                                f"{source_size}|"
                                f"{source_hash}|"
                                f"{psv(source_text)}|"
                                f"{psv(existing[0])}|"
                                "DUPLICATE_HASH_SKIPPED\n"
                            )

                        success = True
                        break

                    class_directory = (
                        FILES_DIR / class_name
                    )

                    class_directory.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    sequence = (
                        counters[
                            "COPIED_VERIFIED"
                        ]
                        + 1
                    )

                    destination_name = (
                        f"F{sequence:05d}_"
                        f"{source_hash[:16]}"
                        f"{output_suffix}"
                    )

                    destination = (
                        class_directory
                        / destination_name
                    )

                    if len(str(destination)) > 220:
                        destination_name = (
                            f"F{sequence:05d}_"
                            f"{source_hash[:12]}"
                            ".dat"
                        )
                        destination = (
                            class_directory
                            / destination_name
                        )

                    temporary = (
                        HOLD_DIR
                        / (
                            ".partial_"
                            f"{os.getpid()}_"
                            f"{record_id}_"
                            f"{source_hash[:12]}"
                        )
                    )

                    shutil.copyfile(
                        source,
                        temporary,
                    )

                    temporary_hash = sha256_file(
                        temporary
                    )

                    if (
                        temporary_hash
                        != source_hash
                    ):
                        raise RuntimeError(
                            "HASH_MISMATCH"
                        )

                    os.replace(
                        temporary,
                        destination,
                    )

                    final_hash = sha256_file(
                        destination
                    )

                    if final_hash != source_hash:
                        raise RuntimeError(
                            (
                                "HASH_MISMATCH_"
                                "AFTER_FINALIZE"
                            )
                        )

                    counters[
                        "COPIED_VERIFIED"
                    ] += 1

                    connection.execute(
                        (
                            "INSERT INTO hashes("
                            "sha256,destination,"
                            "updated"
                            ") VALUES(?,?,?)"
                        ),
                        (
                            source_hash,
                            str(destination),
                            now(),
                        ),
                    )

                    connection.execute(
                        (
                            "INSERT INTO items("
                            "source,status,sha256,"
                            "destination,attempts,"
                            "last_error,updated"
                            ") VALUES(?,?,?,?,?,?,?) "
                            "ON CONFLICT(source) "
                            "DO UPDATE SET "
                            "status=excluded.status,"
                            "sha256=excluded.sha256,"
                            "destination="
                            "excluded.destination,"
                            "attempts="
                            "excluded.attempts,"
                            "last_error=NULL,"
                            "updated=excluded.updated"
                        ),
                        (
                            source_text,
                            "COPIED_VERIFIED",
                            source_hash,
                            str(destination),
                            attempt,
                            None,
                            now(),
                        ),
                    )

                    connection.commit()

                    with MANIFEST.open(
                        "a",
                        encoding="utf-8",
                    ) as manifest_file:
                        manifest_file.write(
                            f"{now()}|"
                            f"{psv(record_id)}|"
                            f"{psv(category)}|"
                            f"{class_name}|"
                            f"{source_size}|"
                            f"{source_hash}|"
                            f"{psv(source_text)}|"
                            f"{psv(destination)}|"
                            "COPIED_VERIFIED\n"
                        )

                    success = True
                    break

                except Exception as exception:
                    last_exception = exception

                    if (
                        "HASH_MISMATCH"
                        in str(exception)
                    ):
                        code = "HASH_MISMATCH"
                    else:
                        code = error_code(
                            exception
                        )

                    error_counts[code] += 1
                    counters["ERRORS"] += 1

                    if (
                        attempt < RETRY_LIMIT
                        and code
                        not in {"NO_SPACE_LEFT"}
                    ):
                        action = "RETRY"
                    else:
                        action = "HOLD_OR_STOP"

                    with ERRORS.open(
                        "a",
                        encoding="utf-8",
                    ) as error_file:
                        error_file.write(
                            f"{now()}|"
                            f"{psv(record_id)}|"
                            f"{attempt}|"
                            f"{code}|"
                            f"{psv(source_text)}|"
                            f"{psv(exception)}|"
                            f"{action}\n"
                        )

                    connection.execute(
                        (
                            "INSERT INTO items("
                            "source,status,attempts,"
                            "last_error,updated"
                            ") VALUES(?,?,?,?,?) "
                            "ON CONFLICT(source) "
                            "DO UPDATE SET "
                            "status=excluded.status,"
                            "attempts="
                            "excluded.attempts,"
                            "last_error="
                            "excluded.last_error,"
                            "updated="
                            "excluded.updated"
                        ),
                        (
                            source_text,
                            (
                                "RETRYING"
                                if attempt
                                < RETRY_LIMIT
                                else "HOLD"
                            ),
                            attempt,
                            code,
                            now(),
                        ),
                    )

                    connection.commit()

                    if code == "NO_SPACE_LEFT":
                        write_status(
                            (
                                "STOPPED_"
                                "NO_SPACE_LEFT"
                            ),
                            counters,
                            current=source_text,
                            note=str(exception),
                        )
                        raise SystemExit(3)

                    if attempt < RETRY_LIMIT:
                        time.sleep(
                            min(
                                30,
                                2**attempt,
                            )
                        )

            if not success:
                counters["HOLD"] += 1

                write_status(
                    "RUNNING",
                    counters,
                    current=source_text,
                    note=(
                        "HELD_AFTER_RETRIES="
                        f"{psv(last_exception)}"
                    ),
                )

            learning_payload = {
                "updated": now(),
                "error_counts": dict(
                    error_counts
                ),
                "rules": rules,
                "adaptive_behavior": {
                    "retry_limit": (
                        RETRY_LIMIT
                    ),
                    "backoff": (
                        "2 and 4 seconds"
                    ),
                    "duplicate_policy": (
                        "actual SHA-256"
                    ),
                    "destination_naming": (
                        "short hash-based names"
                    ),
                    "self_modifying_code": False,
                },
            }

            atomic_write(
                LEARNING,
                json.dumps(
                    learning_payload,
                    indent=2,
                    ensure_ascii=False,
                ),
            )

        else:
            write_status(
                "QUEUE_COMPLETED",
                counters,
                note=(
                    "All repair-plan "
                    "rows processed"
                ),
            )

except SystemExit:
    raise

except Exception:
    counters["ERRORS"] += 1
    error_counts["DAEMON_FATAL"] += 1

    with ERRORS.open(
        "a",
        encoding="utf-8",
    ) as error_file:
        error_file.write(
            f"{now()}|||DAEMON_FATAL||"
            f"{psv(traceback.format_exc())}|"
            "STOPPED\n"
        )

    write_status(
        "FATAL_ERROR",
        counters,
        note=(
            "See ERROR_LEDGER.psv"
        ),
    )

    raise

finally:
    if STATUS.exists():
        final_status_text = (
            STATUS.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )
    else:
        final_status_text = ""

    summary_text = "\n".join(
        [
            (
                "FREYA_REPAIR_DAEMON_"
                "FINAL_SUMMARY"
            ),
            f"CREATED={now()}",
            f"PLAN={PLAN}",
            f"BASE={BASE}",
            (
                "SCANNED="
                f"{counters.get('SCANNED', 0)}"
            ),
            (
                "COPIED_VERIFIED="
                f"{counters.get('COPIED_VERIFIED', 0)}"
            ),
            (
                "DUPLICATE_HASH_SKIPPED="
                f"{counters.get('DUPLICATE_HASH_SKIPPED', 0)}"
            ),
            f"HOLD={counters.get('HOLD', 0)}",
            (
                "ERROR_EVENTS="
                f"{counters.get('ERRORS', 0)}"
            ),
            (
                "ERROR_COUNTS="
                + json.dumps(
                    dict(error_counts),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            ),
            "ORIGINALS_CHANGED=NO",
            "ORIGINALS_MOVED=NO",
            "ORIGINALS_RENAMED=NO",
            "FILES_DELETED=NO",
            "ARCHIVES_OPENED=NO",
            "SCRIPTS_EXECUTED=NO",
            "INTERNET_USED=NO",
            (
                "FINAL_STATUS="
                "SEE_CONTROL_STATUS"
            ),
            "",
            final_status_text,
        ]
    )

    atomic_write(
        SUMMARY,
        summary_text,
    )

    connection.commit()
    connection.close()

    try:
        os.close(lock_fd)
    except Exception:
        pass

    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass
