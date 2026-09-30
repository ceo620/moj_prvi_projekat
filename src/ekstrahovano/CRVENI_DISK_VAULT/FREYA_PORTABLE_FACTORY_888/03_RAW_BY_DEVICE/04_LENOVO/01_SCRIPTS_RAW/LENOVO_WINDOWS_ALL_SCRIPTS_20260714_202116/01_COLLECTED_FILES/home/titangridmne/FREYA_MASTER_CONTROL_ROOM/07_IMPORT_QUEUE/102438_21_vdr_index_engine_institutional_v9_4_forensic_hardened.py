#!/usr/bin/env python3
"""
TITAN 1 — VDR INDEX ENGINE v9.4 FORENSIC HARDENING PATCH
Institutional Realignment | Gap-Aware | Audit-Hardened | File-Based v9.4

This version hardens the v9.4 design against false readiness inflation:
- explicit zero-byte quarantine
- explicit L0_QUARANTINED maturity
- structured external verifier status enum
- status-derived red-flag rules
- dependency validation hook
- atomic manifest/report writes
- hash-chained JSONL ledger events
- local path redaction for lender-facing outputs
- centralized engine version metadata
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ENGINE_VERSION = "v9.4-forensic-hardened"
PROJECT_NAME = "TITAN 1 – Integrated Industrial Ecosystem"
CLASSIFICATION = "Confidential – Internal Institutional Review Draft"
PHASE = "Documentation Completion & Independent Validation Phase"
DOCUMENT_OWNER = "ARS METAL INDUSTRIES DOO"

DEFAULT_TITAN_ROOT = r"C:\Users\Korisnik\Desktop\GEMINI SKRIPTE\TITAN_KERNEL"

DEFAULT_VDR_STUBS = {
    "STUB_1_INFRASTRUCTURE_12_5MW": [],
    "STUB_2_COMMERCIAL_TAKE_OR_PAY": [],
    "STUB_3_ESG_COMPLIANCE_ESIA": [],
    "STUB_4_CORPORATE_GOVERNANCE_SHA": [],
    "STUB_5_CAPEX_RECONCILIATION_BIG4": [],
    "STUB_6_FINANCIAL_MODEL": [],
    "STUB_7_OFFTAKE_AGREEMENTS": [],
    "STUB_8_EPC_CONTRACTS": [],
    "STUB_9_TAX_AND_INSURANCE": [],
}

# SSOT register bridge. This is a mapping layer, not a direct Excel ingestion engine.
DEFAULT_PILLAR_TO_STUB_MAPPING = {
    "00. Financial SSOT & KPIs": "STUB_6_FINANCIAL_MODEL",
    "01. Administration & Governance": "STUB_4_CORPORATE_GOVERNANCE_SHA",
    "02. Legal & Corporate": "STUB_4_CORPORATE_GOVERNANCE_SHA",
    "03. Land & Permitting": "STUB_1_INFRASTRUCTURE_12_5MW",
    "04. Technical Design": "STUB_1_INFRASTRUCTURE_12_5MW",
    "05. EPC & Construction": "STUB_8_EPC_CONTRACTS",
    "06. ESG & Sustainability": "STUB_3_ESG_COMPLIANCE_ESIA",
    "07. Market & Commercial": "STUB_2_COMMERCIAL_TAKE_OR_PAY",
    "08. Finance & Modelling": "STUB_6_FINANCIAL_MODEL",
    "09. Risk Management": "STUB_4_CORPORATE_GOVERNANCE_SHA",
    "10. Sponsor Package": "STUB_4_CORPORATE_GOVERNANCE_SHA",
    "11. PPP & Institutional": "STUB_4_CORPORATE_GOVERNANCE_SHA",
    "12. Reporting & IC": "STUB_5_CAPEX_RECONCILIATION_BIG4",
}


class ExternalVerifierStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    NOT_APPOINTED = "NOT_APPOINTED"
    APPOINTED_PENDING = "APPOINTED_PENDING"
    REVIEW_IN_PROGRESS = "REVIEW_IN_PROGRESS"
    REVIEW_COMPLETE = "REVIEW_COMPLETE"
    LENDER_ACCEPTED = "LENDER_ACCEPTED"
    UNKNOWN = "UNKNOWN"


class DependencyStatus(str, Enum):
    SATISFIED = "SATISFIED"
    NOT_VALIDATED = "NOT_VALIDATED"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class FileAnalysis:
    exists: bool
    size_bytes: Optional[int]
    sha256_hash: Optional[str]
    magic_type: str
    file_error: Optional[str] = None


def _json_dumps_canonical(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:160] or f"doc_{uuid.uuid4().hex[:12]}"


def _parse_iso_date(value: Optional[str]) -> Tuple[Optional[date], Optional[str]]:
    if value in (None, ""):
        return None, "MISSING_DATE"
    try:
        return date.fromisoformat(str(value)), None
    except ValueError:
        return None, "INVALID_DATE_FORMAT"


def _normalize_status(value: Any) -> ExternalVerifierStatus:
    """Normalize a structured enum. Backward-compatible text inference is only fallback."""
    if isinstance(value, ExternalVerifierStatus):
        return value

    if value is None or str(value).strip() == "":
        return ExternalVerifierStatus.UNKNOWN

    raw = str(value).strip().upper()
    if raw in ExternalVerifierStatus.__members__:
        return ExternalVerifierStatus[raw]
    for status in ExternalVerifierStatus:
        if raw == status.value:
            return status

    # Backward compatibility only. New configs should pass external_verifier_status explicitly.
    normalized = str(value).strip().lower()
    if any(phrase in normalized for phrase in ["lender accepted", "accepted by lender"]):
        return ExternalVerifierStatus.LENDER_ACCEPTED
    if any(phrase in normalized for phrase in ["review complete", "completed", "independently reviewed", "final review issued"]):
        if "not completed" not in normalized and "not complete" not in normalized:
            return ExternalVerifierStatus.REVIEW_COMPLETE
    if any(phrase in normalized for phrase in ["in progress", "ongoing", "under review"]):
        return ExternalVerifierStatus.REVIEW_IN_PROGRESS
    if any(phrase in normalized for phrase in ["pending appointment", "not appointed"]):
        return ExternalVerifierStatus.NOT_APPOINTED
    if any(phrase in normalized for phrase in ["pending", "subject to", "awaiting"]):
        return ExternalVerifierStatus.APPOINTED_PENDING
    if any(phrase in normalized for phrase in ["not required", "n/a", "na"]):
        return ExternalVerifierStatus.NOT_REQUIRED

    return ExternalVerifierStatus.UNKNOWN


class TitanVdrInstitutionalCore:
    """
    Hardened standalone implementation for TITAN 1 VDR Index Engine v9.4.

    This class is still intentionally file-based. It introduces forensic controls
    while keeping the future v10 persistence adapter boundary clear.
    """

    def __init__(
        self,
        titan_root: Optional[str] = None,
        *,
        expose_local_paths: bool = False,
        dependency_registry: Optional[Dict[str, str]] = None,
        pillar_to_stub_mapping: Optional[Dict[str, str]] = None,
        duplicate_policy: str = "reject",
    ):
        titan_root = titan_root or os.getenv("TITAN_KERNEL_ROOT", DEFAULT_TITAN_ROOT)
        self.titan_root = Path(titan_root).expanduser().resolve()
        self.reports_dir = self.titan_root / "REPORTS"

        self.vdr_manifest_path = self.reports_dir / "vdr_builder_manifest_v9_4_hardened.json"
        self.audit_ledger_path = self.reports_dir / "vdr_audit_ledger_v9_4_hardened.jsonl"
        self.gap_report_json_path = self.reports_dir / "lender_gap_report_v9_4_hardened.json"
        self.gap_report_csv_path = self.reports_dir / "lender_gap_report_v9_4_hardened.csv"

        self.vdr_structure: Dict[str, List[Dict[str, Any]]] = {
            stub: [] for stub in DEFAULT_VDR_STUBS
        }
        self.expose_local_paths = expose_local_paths
        self.dependency_registry = {
            str(k): str(v).upper() for k, v in (dependency_registry or {}).items()
        }
        self.pillar_to_stub_mapping = pillar_to_stub_mapping or DEFAULT_PILLAR_TO_STUB_MAPPING.copy()
        self.duplicate_policy = duplicate_policy.lower()
        if self.duplicate_policy not in {"reject", "allow"}:
            raise ValueError("duplicate_policy must be 'reject' or 'allow'")

        self._seen_document_ids: set[str] = set()
        self._ledger_sequence_no, self._last_event_hash = self._load_last_ledger_state()

    def now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _load_last_ledger_state(self) -> Tuple[int, Optional[str]]:
        if not self.audit_ledger_path.exists():
            return 0, None
        try:
            last_line = None
            with self.audit_ledger_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line
            if not last_line:
                return 0, None
            last_event = json.loads(last_line)
            return int(last_event.get("sequence_no", 0)), last_event.get("event_hash")
        except Exception:
            # Do not break normal operation, but preserve this in future health checks.
            return 0, None

    def _atomic_write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
            tmp_path.replace(path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def _local_path_payload(self, file_path: Path) -> Dict[str, Any]:
        raw = str(file_path)
        payload = {
            "source_path": file_path.name,
            "source_path_type": "REDACTED_LOCAL_PATH",
            "source_path_fingerprint": _sha256_text(raw),
        }
        if self.expose_local_paths:
            payload["source_path_local"] = raw
            payload["source_path_type"] = "LOCAL_PATH_EXPOSED_INTERNAL_ONLY"
        return payload

    def map_ssot_pillar_to_stub(self, pillar_name: str) -> Optional[str]:
        return self.pillar_to_stub_mapping.get(str(pillar_name).strip())

    def analyze_file(self, filepath: str | Path) -> FileAnalysis:
        path = Path(filepath)
        if not path.exists():
            return FileAnalysis(
                exists=False,
                size_bytes=None,
                sha256_hash=None,
                magic_type="AWAITING_FINAL_SIGNED_COPY",
            )

        try:
            size = path.stat().st_size
        except Exception as exc:
            return FileAnalysis(
                exists=True,
                size_bytes=None,
                sha256_hash=None,
                magic_type="FILE_ERROR",
                file_error=f"STAT_FAILED:{exc.__class__.__name__}",
            )

        if size == 0:
            return FileAnalysis(
                exists=True,
                size_bytes=0,
                sha256_hash=None,
                magic_type="EMPTY_FILE",
            )

        try:
            with path.open("rb") as f:
                header = f.read(16)
        except Exception as exc:
            return FileAnalysis(
                exists=True,
                size_bytes=size,
                sha256_hash=None,
                magic_type="FILE_ERROR",
                file_error=f"READ_HEADER_FAILED:{exc.__class__.__name__}",
            )

        magic_type = self._detect_magic_type_from_header(header)

        sha256_hash = None
        hash_error = None
        try:
            sha256 = hashlib.sha256()
            with path.open("rb") as f:
                for block in iter(lambda: f.read(1024 * 1024), b""):
                    sha256.update(block)
            sha256_hash = sha256.hexdigest()
        except Exception as exc:
            hash_error = f"HASH_FAILED:{exc.__class__.__name__}"

        return FileAnalysis(
            exists=True,
            size_bytes=size,
            sha256_hash=sha256_hash,
            magic_type=magic_type if hash_error is None else "FILE_ERROR",
            file_error=hash_error,
        )

    @staticmethod
    def _detect_magic_type_from_header(header: bytes) -> str:
        if header.startswith(b"%PDF"):
            return "PDF"
        if header.startswith(b"PK"):
            return "ZIP_OR_OFFICE_ARCHITECTURE"
        if header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"):
            return "OLE_COMPOUND_DOCUMENT"
        stripped = header.lstrip()
        if stripped.startswith((b"{", b"[")):
            return "JSON_LIKE"
        return "UNKNOWN"

    def validate_params(self, params: Dict[str, Any], *, file_exists: bool) -> List[str]:
        missing: List[str] = []
        required_fields = ["issuer", "expected_submission_date", "dd_priority"]
        if file_exists:
            required_fields.append("document_date")

        for field in required_fields:
            if params.get(field) in (None, ""):
                missing.append(field)

        _, expected_error = _parse_iso_date(params.get("expected_submission_date"))
        if params.get("expected_submission_date") not in (None, "") and expected_error:
            missing.append("expected_submission_date:INVALID_DATE_FORMAT")

        if params.get("document_date") not in (None, ""):
            _, document_error = _parse_iso_date(params.get("document_date"))
            if document_error:
                missing.append("document_date:INVALID_DATE_FORMAT")

        return missing

    def validate_dependencies(self, dependency_chain: Iterable[str]) -> Tuple[DependencyStatus, List[str]]:
        deps = [str(dep).strip() for dep in dependency_chain or [] if str(dep).strip()]
        if not deps:
            return DependencyStatus.SATISFIED, []

        if not self.dependency_registry:
            return DependencyStatus.NOT_VALIDATED, []

        missing = [dep for dep in deps if dep not in self.dependency_registry]
        if missing:
            return DependencyStatus.MISSING, missing

        blocked = [
            dep for dep in deps
            if self.dependency_registry.get(dep, "").upper() in {"BLOCKED", "MISSING", "FAILED", "NO"}
        ]
        if blocked:
            return DependencyStatus.BLOCKED, blocked

        return DependencyStatus.SATISFIED, []

    def classify_status(
        self,
        analysis: FileAnalysis,
        metadata: Dict[str, Any],
        external_verifier_status: ExternalVerifierStatus,
    ) -> str:
        if not analysis.exists:
            return "SUBJECT_TO_FINAL_EXECUTION"
        if analysis.size_bytes == 0:
            return "QUARANTINE_EMPTY_FILE"
        if analysis.file_error or analysis.sha256_hash is None or analysis.magic_type == "FILE_ERROR":
            return "QUARANTINE_VERIFICATION_FAILED"
        if analysis.magic_type in {"UNKNOWN", "EMPTY_FILE"}:
            return "QUARANTINE_UNVERIFIED_FORMAT"

        missing_metadata = self.validate_params(metadata, file_exists=True)
        if missing_metadata:
            return "METADATA_INCOMPLETE_PENDING_REMEDIATION"

        if external_verifier_status in {
            ExternalVerifierStatus.REVIEW_COMPLETE,
            ExternalVerifierStatus.LENDER_ACCEPTED,
        }:
            return "INDEPENDENT_REVIEW_COMPLETED_PENDING_LENDER_REVIEW"

        if external_verifier_status in {
            ExternalVerifierStatus.NOT_APPOINTED,
            ExternalVerifierStatus.APPOINTED_PENDING,
            ExternalVerifierStatus.REVIEW_IN_PROGRESS,
            ExternalVerifierStatus.UNKNOWN,
        }:
            return "HASHED_PENDING_EXTERNAL_VALIDATION"

        if external_verifier_status == ExternalVerifierStatus.NOT_REQUIRED:
            return "HASHED_VALIDATED_NO_EXTERNAL_REVIEW_REQUIRED"

        return "DOCUMENT_IN_PREPARATION"

    @staticmethod
    def determine_maturity(file_exists: bool, status: str) -> str:
        if status.startswith("QUARANTINE"):
            return "L0_QUARANTINED"
        if not file_exists:
            return "L1_REFERENCE_ONLY"
        if status == "SUBJECT_TO_FINAL_EXECUTION":
            return "L1_REFERENCE_ONLY"
        if status == "METADATA_INCOMPLETE_PENDING_REMEDIATION":
            return "L2_DRAFT_COMPLETED"
        if status in {
            "HASHED_PENDING_EXTERNAL_VALIDATION",
            "HASHED_VALIDATED_NO_EXTERNAL_REVIEW_REQUIRED",
        }:
            return "L3_SIGNED"
        if status == "INDEPENDENT_REVIEW_COMPLETED_PENDING_LENDER_REVIEW":
            return "L4_INDEPENDENTLY_REVIEWED"
        return "L2_DRAFT_COMPLETED"

    def derive_red_flags(
        self,
        *,
        analysis: FileAnalysis,
        lender_status: str,
        metadata: Dict[str, Any],
        missing_metadata: List[str],
        dependency_status: DependencyStatus,
        dependency_issues: List[str],
    ) -> Tuple[str, List[str]]:
        reasons: List[str] = []

        if not analysis.exists:
            reasons.append("PHYSICAL_DOCUMENT_NOT_LOADED")
        if analysis.size_bytes == 0:
            reasons.append("ZERO_BYTE_FILE")
        if analysis.sha256_hash is None and analysis.exists:
            reasons.append("HASH_NOT_GENERATED")
        if analysis.magic_type in {"UNKNOWN", "FILE_ERROR", "EMPTY_FILE"}:
            reasons.append(f"MAGIC_TYPE_{analysis.magic_type}")
        if lender_status.startswith("QUARANTINE"):
            reasons.append(lender_status)
        if missing_metadata:
            reasons.append("MISSING_OR_INVALID_METADATA:" + ",".join(missing_metadata))
        if dependency_status in {DependencyStatus.MISSING, DependencyStatus.BLOCKED}:
            reasons.append(f"DEPENDENCY_{dependency_status.value}:" + ",".join(dependency_issues))

        expected_date, expected_date_error = _parse_iso_date(metadata.get("expected_submission_date"))
        if expected_date_error and metadata.get("expected_submission_date") not in (None, ""):
            reasons.append(f"EXPECTED_SUBMISSION_DATE_{expected_date_error}")
        if (not analysis.exists) and expected_date and expected_date < date.today():
            reasons.append("PAST_DUE_MISSING_EVIDENCE")

        return ("YES" if reasons else "NO"), reasons

    def append_ledger(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self._ledger_sequence_no += 1
        event_with_chain = {
            "event_id": str(uuid.uuid4()),
            "sequence_no": self._ledger_sequence_no,
            "previous_event_hash": self._last_event_hash,
            **event,
        }
        event_hash = _sha256_text(_json_dumps_canonical(event_with_chain))
        event_with_chain["event_hash"] = event_hash

        # Append-only convention, now with tamper-evident hash chaining.
        with self.audit_ledger_path.open("a", encoding="utf-8", newline="") as f:
            f.write(json.dumps(event_with_chain, ensure_ascii=False) + "\n")

        self._last_event_hash = event_hash
        return event_with_chain

    def ingest_document_artifact(
        self,
        stub_name: str,
        doc_name: str,
        file_path: str,
        params: Dict[str, Any],
    ) -> bool:
        if stub_name not in self.vdr_structure:
            rejection = {
                "event_type": "VDR_INDEX_REJECTED_INGESTION",
                "event_timestamp": self.now_iso(),
                "engine_version": ENGINE_VERSION,
                "classification": CLASSIFICATION,
                "phase": PHASE,
                "reason": "INVALID_STUB_NAME",
                "stub_name": stub_name,
                "document_name": doc_name,
            }
            self.append_ledger(rejection)
            raise ValueError(f"Invalid VDR stub_name: {stub_name}")

        document_id = params.get("document_id") or _slug(f"{stub_name}_{doc_name}")
        if document_id in self._seen_document_ids and self.duplicate_policy == "reject":
            rejection = {
                "event_type": "VDR_INDEX_REJECTED_INGESTION",
                "event_timestamp": self.now_iso(),
                "engine_version": ENGINE_VERSION,
                "classification": CLASSIFICATION,
                "phase": PHASE,
                "reason": "DUPLICATE_DOCUMENT_ID_IN_RUN",
                "stub_name": stub_name,
                "document_name": doc_name,
                "document_id": document_id,
            }
            self.append_ledger(rejection)
            raise ValueError(f"Duplicate document_id in run: {document_id}")

        path = Path(file_path)
        analysis = self.analyze_file(path)
        external_verifier_status = _normalize_status(
            params.get("external_verifier_status", params.get("external_verifier"))
        )
        dependency_status, dependency_issues = self.validate_dependencies(params.get("dependency_chain", []))
        missing_metadata = self.validate_params(params, file_exists=analysis.exists)

        lender_status = self.classify_status(analysis, params, external_verifier_status)
        maturity_level = self.determine_maturity(analysis.exists, lender_status)
        red_flag, red_flag_reasons = self.derive_red_flags(
            analysis=analysis,
            lender_status=lender_status,
            metadata=params,
            missing_metadata=missing_metadata,
            dependency_status=dependency_status,
            dependency_issues=dependency_issues,
        )

        evidence_type = "PHYSICAL_DOCUMENT" if analysis.exists else "DOCUMENT_REFERENCE_PENDING_SUBMISSION"
        hash_status = "HASH_GENERATED" if analysis.sha256_hash else "HASH_NOT_AVAILABLE"

        doc_entry: Dict[str, Any] = {
            "document_id": document_id,
            "document_name": doc_name,
            "document_owner": DOCUMENT_OWNER,
            "stub_name": stub_name,
            **self._local_path_payload(path),
            "vdr_relative_path": params.get("vdr_relative_path", path.name),
            "evidence_type": evidence_type,
            "sha256_hash": analysis.sha256_hash,
            "hash_status": hash_status,
            "integrity_status": "HASH_GENERATED_NOT_CONTENT_VALIDATED" if analysis.sha256_hash else "INTEGRITY_NOT_VERIFIED",
            "file_status": "PHYSICAL_COPY_LOADED" if analysis.exists else "AWAITING_FINAL_SIGNED_COPY",
            "file_size_bytes": analysis.size_bytes,
            "magic_type": analysis.magic_type,
            "file_error": analysis.file_error,
            "evidence_maturity_level": maturity_level,
            "lender_readiness_status": lender_status,
            "expected_submission_date": params.get("expected_submission_date", "2026-06-15"),
            "issuer": params.get("issuer"),
            "document_date": params.get("document_date"),
            "external_verifier": params.get("external_verifier", "Subject to Independent Technical Review"),
            "external_verifier_status": external_verifier_status.value,
            "dd_priority": params.get("dd_priority", "P0"),
            "dependency_chain": params.get("dependency_chain", []),
            "dependency_status": dependency_status.value,
            "dependency_issues": dependency_issues,
            "red_flag": red_flag,
            "red_flag_reason": "; ".join(red_flag_reasons) if red_flag_reasons else None,
            "red_flag_reasons": red_flag_reasons,
            "final_use_allowed": "NO",
            "external_distribution_allowed": "NO",
            "lender_submission_allowed": "NO",
            "reliance_status": "NON_RELIANCE_INTERNAL_REVIEW_ONLY",
            "ingestion_timestamp": self.now_iso(),
        }

        self.vdr_structure[stub_name].append(doc_entry)
        self._seen_document_ids.add(document_id)

        ledger_event = {
            "event_type": "VDR_INDEX_REALIGNMENT",
            "event_timestamp": self.now_iso(),
            "engine_version": ENGINE_VERSION,
            "classification": CLASSIFICATION,
            "phase": PHASE,
            "document_entry": doc_entry,
        }
        self.append_ledger(ledger_event)
        print(f"[+] Ingested Artifact: {doc_name} → {stub_name} | red_flag={red_flag} | maturity={maturity_level}")
        return True

    def calculate_institutional_readiness_score(self) -> Dict[str, Any]:
        docs = [doc for stub_docs in self.vdr_structure.values() for doc in stub_docs]
        total_docs = len(docs)
        red_flag_count = sum(1 for doc in docs if doc.get("red_flag") == "YES")
        quarantine_count = sum(
            1 for doc in docs
            if str(doc.get("lender_readiness_status", "")).startswith("QUARANTINE")
        )

        p0_docs = [doc for doc in docs if doc.get("dd_priority") == "P0"]
        complete_p0_docs = [
            doc for doc in p0_docs
            if doc.get("red_flag") == "NO"
            and doc.get("evidence_maturity_level") in {"L3_SIGNED", "L4_INDEPENDENTLY_REVIEWED"}
        ]

        total_p0 = len(p0_docs)
        p0_score = (len(complete_p0_docs) / total_p0 * 100) if total_p0 > 0 else 100.0
        non_red_flag_rate = ((total_docs - red_flag_count) / max(total_docs, 1) * 100)

        overall_score = round((0.7 * p0_score) + (0.3 * non_red_flag_rate), 1)

        return {
            "overall_readiness_percent": overall_score,
            "p0_documents": total_p0,
            "p0_completed": len(complete_p0_docs),
            "p0_completion_rate": round(p0_score, 1),
            "total_documents": total_docs,
            "red_flag_count": red_flag_count,
            "quarantine_count": quarantine_count,
            "non_red_flag_document_rate": round(non_red_flag_rate, 1),
            "score_policy": "0.7*p0_completion_rate + 0.3*non_red_flag_document_rate",
        }

    def build_vdr_manifest(self) -> Path:
        total_docs = sum(len(v) for v in self.vdr_structure.values())
        p0_docs = sum(
            1 for docs in self.vdr_structure.values()
            for doc in docs if doc.get("dd_priority") == "P0"
        )
        pending_docs = sum(
            1 for docs in self.vdr_structure.values()
            for doc in docs if doc.get("file_status") == "AWAITING_FINAL_SIGNED_COPY"
        )

        manifest_data = {
            "document_metadata": {
                "project_name": PROJECT_NAME,
                "document_version": ENGINE_VERSION,
                "classification": CLASSIFICATION,
                "phase": PHASE,
                "last_audit_update": self.now_iso(),
                "readiness_score": self.calculate_institutional_readiness_score(),
                "local_paths_exposed": self.expose_local_paths,
            },
            "summary": {
                "total_documents": total_docs,
                "p0_documents": p0_docs,
                "documents_pending_submission": pending_docs,
            },
            "vdr_index": self.vdr_structure,
        }

        self._atomic_write_text(
            self.vdr_manifest_path,
            json.dumps(manifest_data, indent=4, ensure_ascii=False),
        )
        print(f"[✓] Hardened VDR Manifest generated → {self.vdr_manifest_path}")
        return self.vdr_manifest_path

    def generate_lender_gap_report(self) -> Tuple[Path, Path]:
        gap_rows: List[Dict[str, Any]] = []
        for stub_name, docs in self.vdr_structure.items():
            for doc in docs:
                gap_rows.append({
                    "document_id": doc.get("document_id"),
                    "stub": stub_name,
                    "document_name": doc.get("document_name"),
                    "vdr_relative_path": doc.get("vdr_relative_path"),
                    "dd_priority": doc.get("dd_priority"),
                    "lender_readiness_status": doc.get("lender_readiness_status"),
                    "evidence_maturity_level": doc.get("evidence_maturity_level"),
                    "red_flag": doc.get("red_flag"),
                    "red_flag_reason": doc.get("red_flag_reason"),
                    "expected_submission_date": doc.get("expected_submission_date"),
                    "issuer": doc.get("issuer"),
                    "document_date": doc.get("document_date"),
                    "external_verifier_status": doc.get("external_verifier_status"),
                    "dependency_chain": ", ".join(doc.get("dependency_chain", [])),
                    "dependency_status": doc.get("dependency_status"),
                    "dependency_issues": ", ".join(doc.get("dependency_issues", [])),
                    "file_status": doc.get("file_status"),
                    "file_size_bytes": doc.get("file_size_bytes"),
                    "magic_type": doc.get("magic_type"),
                    "hash_status": doc.get("hash_status"),
                    "sha256_hash": doc.get("sha256_hash") or "—",
                    "ingestion_timestamp": doc.get("ingestion_timestamp"),
                })

        report = {
            "report_metadata": {
                "project": PROJECT_NAME,
                "version": ENGINE_VERSION,
                "classification": CLASSIFICATION,
                "phase": PHASE,
                "generated": self.now_iso(),
                "readiness_score": self.calculate_institutional_readiness_score(),
                "local_paths_exposed": False,
            },
            "gap_summary": gap_rows,
        }

        self._atomic_write_text(
            self.gap_report_json_path,
            json.dumps(report, indent=2, ensure_ascii=False),
        )

        output = io.StringIO()
        if gap_rows:
            writer = csv.DictWriter(output, fieldnames=list(gap_rows[0].keys()))
            writer.writeheader()
            writer.writerows(gap_rows)
        else:
            # Preserve a useful empty CSV for automation.
            output.write("document_id,stub,document_name,red_flag,lender_readiness_status\n")

        self._atomic_write_text(self.gap_report_csv_path, output.getvalue())

        print(f"[✓] Hardened Lender Gap Report JSON → {self.gap_report_json_path}")
        print(f"[✓] Hardened Lender Gap Report CSV  → {self.gap_report_csv_path}")
        return self.gap_report_json_path, self.gap_report_csv_path

    def verify_ledger_chain(self) -> Dict[str, Any]:
        if not self.audit_ledger_path.exists():
            return {"ledger_exists": False, "valid": True, "events_checked": 0}

        previous_hash = None
        events_checked = 0
        errors: List[str] = []

        with self.audit_ledger_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"line_{idx}:INVALID_JSON")
                    continue

                event_hash = event.get("event_hash")
                declared_previous = event.get("previous_event_hash")
                if declared_previous != previous_hash:
                    errors.append(f"line_{idx}:PREVIOUS_HASH_MISMATCH")

                event_without_hash = dict(event)
                event_without_hash.pop("event_hash", None)
                recomputed = _sha256_text(_json_dumps_canonical(event_without_hash))
                if recomputed != event_hash:
                    errors.append(f"line_{idx}:EVENT_HASH_MISMATCH")

                previous_hash = event_hash
                events_checked += 1

        return {
            "ledger_exists": True,
            "valid": not errors,
            "events_checked": events_checked,
            "errors": errors,
        }


def run_sample_ingestion() -> None:
    builder = TitanVdrInstitutionalCore()

    builder.ingest_document_artifact(
        stub_name="STUB_1_INFRASTRUCTURE_12_5MW",
        doc_name="CEDIS_Energetska_Saglasnost_12_5MW_Signed.pdf",
        file_path=r"C:\Users\Korisnik\Desktop\REVIZIJE\CEDIS_Energetska_Saglasnost_12_5MW_Signed.pdf",
        params={
            "document_id": "CEDIS_GRID_APPROVAL_12_5MW",
            "issuer": "CEDIS",
            "document_date": "2026-05-06",
            "expected_submission_date": "2026-06-15",
            "external_verifier": "Independent Technical Advisor (Pending Appointment)",
            "external_verifier_status": "NOT_APPOINTED",
            "dd_priority": "P0",
            "dependency_chain": ["GRID_CONNECTION_APPROVAL", "ESIA_COMPLETION", "TECHNICAL_DD"],
            "vdr_relative_path": "STUB_1_INFRASTRUCTURE_12_5MW/CEDIS_Energetska_Saglasnost_12_5MW_Signed.pdf",
        },
    )

    builder.ingest_document_artifact(
        stub_name="STUB_3_ESG_COMPLIANCE_ESIA",
        doc_name="EBRD_PR1_PR10_ESIA_Final_Draft.pdf",
        file_path=r"C:\Users\Korisnik\Desktop\REVIZIJE\EBRD_PR1_PR10_ESIA_Final_Draft.pdf",
        params={
            "document_id": "EBRD_PR1_PR10_ESIA_FINAL_DRAFT",
            "issuer": "Environmental Protection Agency",
            "document_date": None,
            "expected_submission_date": "2026-07-20",
            "external_verifier": "Subject to Independent Environmental Review",
            "external_verifier_status": "REVIEW_IN_PROGRESS",
            "dd_priority": "P0",
            "dependency_chain": ["PUBLIC_CONSULTATION_CLOSURE", "SEP_APPROVAL"],
            "vdr_relative_path": "STUB_3_ESG_COMPLIANCE_ESIA/EBRD_PR1_PR10_ESIA_Final_Draft.pdf",
        },
    )

    builder.build_vdr_manifest()
    builder.generate_lender_gap_report()
    score = builder.calculate_institutional_readiness_score()
    ledger_health = builder.verify_ledger_chain()
    print(f"[★] Institutional Readiness Score: {score['overall_readiness_percent']}%")
    print(f"[✓] Ledger Chain Valid: {ledger_health['valid']} ({ledger_health['events_checked']} events checked)")


if __name__ == "__main__":
    run_sample_ingestion()
