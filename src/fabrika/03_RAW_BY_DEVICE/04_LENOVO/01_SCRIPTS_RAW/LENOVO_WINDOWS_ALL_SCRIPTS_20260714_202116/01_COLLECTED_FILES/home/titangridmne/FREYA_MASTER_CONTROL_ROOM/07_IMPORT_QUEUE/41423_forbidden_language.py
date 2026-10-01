# ==============================================================
# 🛡️ BEBA DELTA OMNI-ENFORCER | KROVNI CFO KANON (NEPROBOJNO)
# ==============================================================
import os

TITAN_CANON = {
    "TOTAL_CAPEX": "27,800,000.00 EUR",
    "EQUIPMENT": "18,200,000.00 EUR",
    "KNOW_HOW": "6,500,000.00 EUR",
    "ESG": "3,100,000.00 EUR"
}

# Zakucavanje varijabli u sistemsko okruzenje OS-a
for key, val in TITAN_CANON.items():
    os.environ[f"BEBA_DELTA_{key}"] = val
# ==============================================================

﻿# PROPOSAL_ONLY
# HUMAN_REVIEW_REQUIRED
# WRITE_APPROVED_FOR_FORBIDDEN_LANGUAGE_MODULE_ONLY
# NO_EXECUTION_AUTHORIZED

"""
DELTA v0.1 Forbidden-Language Detector

Purpose:
- Detect prohibited wording in approved text snippets.
- Produce redacted findings only.
- Store no full document body.
- Perform no filesystem mutation, network access, upload, or script execution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


class ForbiddenLanguageError(RuntimeError):
    """Raised when forbidden-language scanning fails safely."""


@dataclass(frozen=True)
class ForbiddenTermRule:
    term_key: str
    pattern: str
    severity: str


@dataclass(frozen=True)
class ForbiddenLanguageFinding:
    finding_id: str
    evidence_id: str | None
    source_field: str
    term_key: str
    severity: str
    matched_text_redacted: str


DEFAULT_RULES: tuple[ForbiddenTermRule, ...] = (
    ForbiddenTermRule(
        term_key="bankability_overclaim",
        pattern=r"\bbankable\b",
        severity="HIGH",
    ),
    ForbiddenTermRule(
        term_key="completion_overclaim",
        pattern=r"\bfinal\b",
        severity="MEDIUM",
    ),
    ForbiddenTermRule(
        term_key="lender_readiness_overclaim",
        pattern=r"\blender[-_\s]?ready\b",
        severity="HIGH",
    ),
    ForbiddenTermRule(
        term_key="guarantee_overclaim",
        pattern=r"\bguaranteed\b|\brisk[-_\s]?free\b|\bautomatic approval\b",
        severity="HIGH",
    ),
    ForbiddenTermRule(
        term_key="governance_bypass",
        pattern=r"\bskip review\b|\bno review needed\b|\bapproval automatic\b",
        severity="HIGH",
    ),
    ForbiddenTermRule(
        term_key="secret_like_marker",
        pattern=r"\bapi[_-]?key\b|\bsecret\b|\btoken\b|\bpassword\b|\bcredential\b",
        severity="CRITICAL",
    ),
)


def redact_match(value: str, start: int, end: int, context: int = 24) -> str:
    if context < 0:
        raise ForbiddenLanguageError("context cannot be negative.")

    prefix_start = max(0, start - context)
    suffix_end = min(len(value), end + context)

    prefix = value[prefix_start:start]
    suffix = value[end:suffix_end]

    return f"{prefix}[REDACTED_MATCH]{suffix}"


def make_finding_id(
    evidence_id: str | None,
    source_field: str,
    term_key: str,
    matched_text_redacted: str,
) -> str:
    raw = f"{evidence_id or ''}|{source_field}|{term_key}|{matched_text_redacted}"
    return sha256(raw.encode("utf-8")).hexdigest()


def scan_text_for_forbidden_language(
    text: str,
    source_field: str,
    evidence_id: str | None = None,
    rules: Iterable[ForbiddenTermRule] = DEFAULT_RULES,
) -> tuple[ForbiddenLanguageFinding, ...]:
    """
    Scan approved text already supplied by caller.

    This function:
    - does not open files
    - does not write files
    - does not store full source text
    - returns redacted findings only
    """

    if not source_field.strip():
        raise ForbiddenLanguageError("Missing source_field.")

    findings: list[ForbiddenLanguageFinding] = []

    for rule in rules:
        if not rule.term_key.strip():
            raise ForbiddenLanguageError("Rule missing term_key.")

        if not rule.pattern.strip():
            raise ForbiddenLanguageError(f"Rule missing pattern: {rule.term_key}")

        for match in re.finditer(rule.pattern, text, flags=re.IGNORECASE):
            redacted = redact_match(text, match.start(), match.end())

            findings.append(
                ForbiddenLanguageFinding(
                    finding_id=make_finding_id(
                        evidence_id=evidence_id,
                        source_field=source_field,
                        term_key=rule.term_key,
                        matched_text_redacted=redacted,
                    ),
                    evidence_id=evidence_id,
                    source_field=source_field,
                    term_key=rule.term_key,
                    severity=rule.severity,
                    matched_text_redacted=redacted,
                )
            )

    return tuple(findings)


def summarize_findings(
    findings: Iterable[ForbiddenLanguageFinding],
) -> dict[str, int]:
    items = tuple(findings)

    by_severity: dict[str, int] = {}
    for finding in items:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1

    return {
        "finding_count": len(items),
        "severity_count": len(by_severity),
    }
