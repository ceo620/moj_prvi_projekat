#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TITAN_DB_SNAPSHOT_ENGINE.py

TITAN 11 - SQLite Snapshot Engine v1.0 HARDENED
Phase:
    DATABASE_SNAPSHOT / Step 6.5

Purpose:
    Creates point-in-time SQLite snapshots before critical operations:
        - signal extraction
        - forensic validation
        - reconciliation
        - control tower sync
        - strategic decision engine

Features:
    - Standard library only.
    - Uses SQLite backup API, not raw copy while DB is live.
    - Runs PRAGMA integrity_check before snapshot.
    - Runs WAL checkpoint before snapshot when possible.
    - Computes SHA256 for snapshot file.
    - Writes manifest JSON + audit JSONL.
    - Rotation policy: keep latest N snapshots.
    - Dry-run mode.
    - Optional VACUUM INTO mode for compact snapshot.

Recommended usage:
    python TITAN_DB_SNAPSHOT_ENGINE_v1_0_HARDENED.py ^
      --db-path "C:\\TITAN\\TITAN_11\\KERNEL\\03_ORCHESTRATION\\v29_state.db" ^
      --snapshot-dir "C:\\TITAN\\TITAN_11\\KERNEL\\14_BACKUPS\\db_snapshots" ^
      --label "before_signal_extraction"

Dry-run:
    python TITAN_DB_SNAPSHOT_ENGINE_v1_0_HARDENED.py --db-path "...\\v29_state.db" --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_NAME = "TITAN_DB_SNAPSHOT_ENGINE.py"
SCRIPT_VERSION = "1.0-HARDENED"
SYSTEM_NAME = "TITAN 11 Enterprise Decision Intelligence Platform"


@dataclass
class SnapshotEvent:
    timestamp_utc: str
    event_type: str
    object_name: str
    status: str
    details: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp_for_filename() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def setup_logging(log_path: Path, verbose: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_label(label: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in label.strip())
    return cleaned[:80] if cleaned else "snapshot"


def connect_sqlite(db_path: Path, readonly: bool = False) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    if readonly:
        uri = f"file:{db_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(str(db_path))

    conn.row_factory = sqlite3.Row
    return conn


class TitanDbSnapshotEngine:
    def __init__(
        self,
        db_path: Path,
        snapshot_dir: Path,
        label: str,
        keep_last: int,
        dry_run: bool,
        use_vacuum_into: bool,
        skip_integrity_check: bool,
    ) -> None:
        self.db_path = db_path.expanduser().resolve()
        self.snapshot_dir = snapshot_dir.expanduser().resolve()
        self.label = safe_label(label)
        self.keep_last = keep_last
        self.dry_run = dry_run
        self.use_vacuum_into = use_vacuum_into
        self.skip_integrity_check = skip_integrity_check
        self.events: List[SnapshotEvent] = []

    def event(self, event_type: str, object_name: str, status: str, details: str) -> None:
        evt = SnapshotEvent(utc_now(), event_type, object_name, status, details)
        self.events.append(evt)
        logging.info("%s | %s | %s | %s", event_type, status, object_name, details)

    def integrity_check(self) -> str:
        if self.skip_integrity_check:
            self.event("INTEGRITY_CHECK", str(self.db_path), "SKIPPED", "Skipped by parameter.")
            return "skipped"

        conn = connect_sqlite(self.db_path, readonly=True)
        try:
            result = conn.execute("PRAGMA integrity_check;").fetchone()
            value = str(result[0]) if result else "unknown"
            status = "OK" if value.lower() == "ok" else "FAILED"
            self.event("INTEGRITY_CHECK", str(self.db_path), status, value)
            return value
        finally:
            conn.close()

    def wal_checkpoint(self) -> Dict[str, Any]:
        conn = connect_sqlite(self.db_path, readonly=False)
        try:
            try:
                row = conn.execute("PRAGMA wal_checkpoint(FULL);").fetchone()
                payload = dict(row) if isinstance(row, sqlite3.Row) else {"result": list(row) if row else []}
                self.event("WAL_CHECKPOINT", str(self.db_path), "OK", json.dumps(payload, ensure_ascii=False))
                return payload
            except sqlite3.DatabaseError as exc:
                self.event("WAL_CHECKPOINT", str(self.db_path), "WARNING", str(exc))
                return {"warning": str(exc)}
        finally:
            conn.close()

    def snapshot_name(self) -> str:
        stem = self.db_path.stem
        return f"{stem}_{self.label}_{timestamp_for_filename()}.db"

    def create_snapshot_backup_api(self, target_path: Path) -> None:
        source = connect_sqlite(self.db_path, readonly=True)
        target = sqlite3.connect(str(target_path))
        try:
            source.backup(target, pages=500, progress=None)
            target.commit()
        finally:
            target.close()
            source.close()

    def create_snapshot_vacuum_into(self, target_path: Path) -> None:
        conn = connect_sqlite(self.db_path, readonly=False)
        try:
            # VACUUM INTO requires literal path escaping.
            escaped = str(target_path).replace("'", "''")
            conn.execute(f"VACUUM INTO '{escaped}';")
            conn.commit()
        finally:
            conn.close()

    def rotate_snapshots(self) -> List[str]:
        if self.keep_last <= 0:
            self.event("ROTATION", str(self.snapshot_dir), "SKIPPED", "keep_last <= 0")
            return []

        pattern = f"{self.db_path.stem}_*.db"
        snapshots = sorted(
            self.snapshot_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )

        removed: List[str] = []
        for old in snapshots[self.keep_last:]:
            try:
                if not self.dry_run:
                    old.unlink()
                    # Remove common sidecars if present.
                    for suffix in [".db-wal", ".db-shm"]:
                        sidecar = Path(str(old) + suffix)
                        if sidecar.exists():
                            sidecar.unlink()
                removed.append(str(old))
                self.event("ROTATION", str(old), "REMOVED" if not self.dry_run else "WOULD_REMOVE", "Old snapshot rotated out.")
            except OSError as exc:
                self.event("ROTATION", str(old), "WARNING", f"Could not remove old snapshot: {exc}")

        return removed

    def write_audit_and_manifest(self, manifest: Dict[str, Any]) -> None:
        if self.dry_run:
            return

        audit_path = self.snapshot_dir / "snapshot_audit_log_v1_0.jsonl"
        manifest_path = self.snapshot_dir / "snapshot_manifest_latest.json"
        run_manifest_path = self.snapshot_dir / f"snapshot_manifest_{timestamp_for_filename()}.json"

        with audit_path.open("a", encoding="utf-8") as f:
            for event in self.events:
                f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        run_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    def run(self) -> Dict[str, Any]:
        started = time.time()

        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.db_path}")

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.event("START", str(self.db_path), "OK", f"Snapshot label={self.label}")

        db_size = self.db_path.stat().st_size
        integrity = self.integrity_check()
        if integrity.lower() != "ok" and integrity != "skipped":
            raise RuntimeError(f"SQLite integrity_check failed: {integrity}")

        checkpoint_result = self.wal_checkpoint()

        target_path = self.snapshot_dir / self.snapshot_name()

        if self.dry_run:
            self.event("SNAPSHOT", str(target_path), "WOULD_CREATE", "Dry-run: snapshot not written.")
            sha = ""
            snapshot_size = 0
        else:
            if self.use_vacuum_into:
                self.create_snapshot_vacuum_into(target_path)
                method = "VACUUM_INTO"
            else:
                self.create_snapshot_backup_api(target_path)
                method = "SQLITE_BACKUP_API"

            sha = sha256_file(target_path)
            snapshot_size = target_path.stat().st_size
            self.event("SNAPSHOT", str(target_path), "CREATED", f"method={method}; sha256={sha}")

        removed = self.rotate_snapshots()

        elapsed = round(time.time() - started, 4)
        manifest = {
            "system_name": SYSTEM_NAME,
            "script_name": SCRIPT_NAME,
            "script_version": SCRIPT_VERSION,
            "generated_at_utc": utc_now(),
            "dry_run": self.dry_run,
            "db_path": str(self.db_path),
            "db_size_bytes": db_size,
            "snapshot_dir": str(self.snapshot_dir),
            "snapshot_path": str(target_path),
            "snapshot_size_bytes": snapshot_size,
            "snapshot_sha256": sha,
            "label": self.label,
            "integrity_check": integrity,
            "wal_checkpoint": checkpoint_result,
            "method": "VACUUM_INTO" if self.use_vacuum_into else "SQLITE_BACKUP_API",
            "keep_last": self.keep_last,
            "rotated_removed": removed,
            "elapsed_seconds": elapsed,
            "events": [asdict(e) for e in self.events],
            "next_recommended_step": "Proceed to the next critical phase only if integrity_check == 'ok' and snapshot file exists.",
        }

        self.write_audit_and_manifest(manifest)
        return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TITAN SQLite Snapshot Engine v1.0 HARDENED")
    parser.add_argument("--db-path", required=True, help="SQLite database path.")
    parser.add_argument("--snapshot-dir", default="./KERNEL/14_BACKUPS/db_snapshots", help="Snapshot output directory.")
    parser.add_argument("--label", default="manual_checkpoint", help="Snapshot label, e.g. before_signal_extraction.")
    parser.add_argument("--keep-last", type=int, default=10, help="Keep latest N snapshots. Default: 10.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vacuum-into", action="store_true", help="Use VACUUM INTO instead of SQLite backup API.")
    parser.add_argument("--skip-integrity-check", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_dir = Path(args.snapshot_dir).expanduser().resolve()
    setup_logging(snapshot_dir / "snapshot_engine.log", args.verbose)

    try:
        engine = TitanDbSnapshotEngine(
            db_path=Path(args.db_path),
            snapshot_dir=snapshot_dir,
            label=args.label,
            keep_last=args.keep_last,
            dry_run=args.dry_run,
            use_vacuum_into=args.vacuum_into,
            skip_integrity_check=args.skip_integrity_check,
        )
        manifest = engine.run()
        print(json.dumps({k: v for k, v in manifest.items() if k != "events"}, indent=2, ensure_ascii=False))
        print("\nTITAN_DB_SNAPSHOT_ENGINE completed.")
        return 0

    except Exception as exc:
        logging.exception("Snapshot engine failed: %s", exc)
        print(f"\nTITAN_DB_SNAPSHOT_ENGINE failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
