from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(os.environ["FREYA_ROOT"]).resolve()
BATCH01 = Path(os.environ["FREYA_BATCH01"]).resolve()
BATCH02 = Path(os.environ["FREYA_BATCH02"]).resolve()
EVIDENCE = Path(os.environ["FREYA_EVIDENCE"]).resolve()

INVENTORY_FILE = BATCH01 / "GLOBAL_INVENTORY.jsonl"
AGENT_REPORT_FILE = BATCH02 / "CANONICAL_AGENT_REPORT.json"

TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".md",
    ".txt",
    ".csv",
    ".tsv",
    ".py",
    ".sh",
    ".bash",
}

CONFIG_SUFFIXES = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
}

STRONG_DOCTRINE_TERMS = {
    "doctrine",
    "doktrina",
    "policy",
    "governance",
    "human_gate",
    "human-gate",
    "security_policy",
    "security-policy",
    "protocol_888",
    "protocol-888",
    "ssot",
}

CONTENT_DOCTRINE_MARKERS = {
    "doctrine_id": 8,
    "doctrine id": 8,
    "doctrine_name": 5,
    "doctrine name": 5,
    "doctrine_version": 4,
    "doctrine version": 4,
    "doctrine_reference": 4,
    "protocol=888": 3,
    "protocol: 888": 3,
    "human_gate": 3,
    "human gate": 3,
    "default_mode=deny": 3,
    "fail_closed": 3,
    "fail closed": 3,
    "ssot": 2,
    "scope": 1,
    "owner": 1,
    "status": 1,
    "rules": 1,
    "prohibitions": 1,
    "forbidden": 1,
    "priority": 1,
    "version": 1,
}

ARCHIVE_TERMS = {
    "archive",
    "arhiva",
    "backup",
    "legacy",
    "deprecated",
    "obsolete",
    "old",
    "previous",
    "quarantine",
}

EVIDENCE_TERMS = {
    "/evidence/",
    "/receipts/",
    "/receipt/",
    "/logs/",
    "/batch_runs/",
    "/reports/",
    "/outbox/",
    "/inbox/",
}

VALIDATOR_TERMS = {
    "validator",
    "validation",
    "verify",
    "verification",
    "health_check",
    "self_test",
    "syntax_check",
    "integrity_check",
}

OUTPUT_TERMS = {
    "output",
    "evidence",
    "receipt",
    "ack",
    "manifest",
    "package",
    "report",
    "outbox",
    "final_seal",
    "final-seal",
}

CANONICAL_AREA_TERMS = {
    "/00_control/",
    "/04_config",
    "/05_agents/",
    "/12_android_mac_24h/",
    "/governance/",
    "/security/",
    "/doctrine",
    "/policy",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def read_text(path: Path, limit: int = 2 * 1024 * 1024) -> str:
    try:
        with path.open("rb") as stream:
            data = stream.read(limit)

        if b"\x00" in data:
            return ""

        return data.decode("utf-8", errors="replace")

    except Exception:
        return ""


def normalize_identifier(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip().strip("\"'")

    if not text:
        return None

    if text.lower() in {
        "none",
        "null",
        "missing",
        "unknown",
        "<dynamic>",
    }:
        return None

    return text


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}

    aliases = {
        "doctrine_id": {
            "doctrine_id",
            "doctrine id",
            "doctrine-id",
            "id doctrine",
        },
        "name": {
            "doctrine_name",
            "doctrine name",
            "name",
            "title",
            "naziv",
        },
        "version": {
            "doctrine_version",
            "doctrine version",
            "version",
            "verzija",
        },
        "scope": {
            "scope",
            "doctrine_scope",
            "doctrine scope",
        },
        "owner": {
            "owner",
            "vlasnik",
            "authority",
        },
        "status": {
            "status",
            "doctrine_status",
            "doctrine status",
        },
        "date": {
            "date",
            "datum",
            "effective_date",
            "created_at",
        },
        "priority": {
            "priority",
            "conflict_priority",
            "precedence",
        },
    }

    reverse_aliases = {
        alias.lower(): canonical
        for canonical, values in aliases.items()
        for alias in values
    }

    for raw_line in text.splitlines()[:500]:
        line = raw_line.strip()

        if not line or line.startswith(("#", "//", ";")):
            line = line.lstrip("#/; ").strip()

        match = re.match(
            r"^([A-Za-z0-9_. -]{2,60})\s*[:=]\s*(.{1,500})$",
            line,
        )

        if not match:
            continue

        key = match.group(1).strip().lower().replace("-", "_")
        value = match.group(2).strip().rstrip(",")

        canonical = reverse_aliases.get(key)

        if canonical and canonical not in metadata:
            metadata[canonical] = value.strip("\"'")

    return metadata


def path_is_archive(path_lower: str) -> bool:
    components = {
        component
        for component in re.split(r"[/_. -]+", path_lower)
        if component
    }

    return bool(components.intersection(ARCHIVE_TERMS))


def doctrine_score(path: Path, text: str) -> tuple[int, list[str]]:
    path_lower = str(path).lower()
    text_lower = text[:1048576].lower()

    score = 0
    reasons: list[str] = []

    for term in STRONG_DOCTRINE_TERMS:
        if term in path_lower:
            score += 6
            reasons.append(f"PATH:{term}")

    for marker, weight in CONTENT_DOCTRINE_MARKERS.items():
        if marker in text_lower:
            score += weight
            reasons.append(f"CONTENT:{marker}")

    explicit_id = bool(
        re.search(
            r"\bdoctrine[ _-]?id\s*[:=]",
            text_lower,
        )
    )

    if explicit_id:
        score += 8
        reasons.append("EXPLICIT_DOCTRINE_ID")

    rules_count = len(
        re.findall(
            r"\b(rule|rules|prohibition|forbidden|must|shall|deny)\b",
            text_lower,
        )
    )

    if rules_count >= 3:
        score += 2
        reasons.append("MULTIPLE_RULE_MARKERS")

    return score, sorted(set(reasons))


def classify_initial(
    path: Path,
    metadata: dict[str, str],
    completeness_missing: list[str],
    score: int,
) -> str:
    path_lower = str(path).lower()
    status = metadata.get("status", "").lower()

    if path_is_archive(path_lower):
        return "LEGACY" if "legacy" in path_lower else "ARCHIVE"

    if any(
        marker in status
        for marker in {
            "legacy",
            "deprecated",
            "obsolete",
            "archive",
            "retired",
        }
    ):
        return "LEGACY"

    if completeness_missing:
        return "INCOMPLETE"

    canonical_location = (
        str(path).startswith(str(ROOT))
        and any(term in path_lower for term in CANONICAL_AREA_TERMS)
    )

    active_status = any(
        marker in status
        for marker in {
            "active",
            "approved",
            "canonical",
            "effective",
            "released",
        }
    )

    if canonical_location and active_status:
        return "ACTIVE"

    if canonical_location and score >= 14:
        return "CANONICAL_CANDIDATE"

    if score >= 18:
        return "CANONICAL_CANDIDATE"

    return "UNKNOWN"


def tokenise(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.lower())
        if len(token) >= 4
        and token not in {
            "agent",
            "android",
            "freya",
            "system",
            "class",
            "module",
        }
    }


def relevance_score(
    path: str,
    text: str,
    terms: set[str],
    exact_values: list[str],
) -> int:
    path_lower = path.lower()
    text_lower = text[:1048576].lower()
    score = 0

    for value in exact_values:
        normalized = value.lower().strip()

        if normalized and normalized in text_lower:
            score += 12

        if normalized and normalized in path_lower:
            score += 8

    for term in terms:
        if term in path_lower:
            score += 3

        if re.search(rf"\b{re.escape(term)}\b", text_lower):
            score += 2

    return score


inventory: list[dict[str, Any]] = []

with INVENTORY_FILE.open("r", encoding="utf-8") as stream:
    for line in stream:
        line = line.strip()

        if not line:
            continue

        try:
            inventory.append(json.loads(line))
        except json.JSONDecodeError:
            continue

agent_report = json.loads(
    AGENT_REPORT_FILE.read_text(encoding="utf-8")
)

canonical_agents: list[dict[str, Any]] = list(
    agent_report.get("canonical_agents", [])
)

if len(canonical_agents) != 10:
    print("STATUS=FAIL")
    print(
        "ERROR=EXPECTED_10_CANONICAL_AGENTS_"
        f"FOUND_{len(canonical_agents)}"
    )
    raise SystemExit(2)

candidate_records: list[dict[str, Any]] = []
text_cache: dict[str, str] = {}

for record in inventory:
    if record.get("type") != "FILE":
        continue

    raw_path = record.get("path")

    if not raw_path:
        continue

    path = Path(raw_path)
    suffix = path.suffix.lower()
    size = int(record.get("size") or 0)
    path_lower = str(path).lower()

    if suffix not in TEXT_SUFFIXES:
        continue

    if size > 2 * 1024 * 1024:
        continue

    path_signal = any(
        term in path_lower
        for term in STRONG_DOCTRINE_TERMS
    )

    canonical_area = (
        str(path).startswith(str(ROOT))
        and any(
            term in path_lower
            for term in CANONICAL_AREA_TERMS
        )
    )

    structured_candidate = (
        suffix in CONFIG_SUFFIXES
        and canonical_area
    )

    if not (
        path_signal
        or canonical_area
        or structured_candidate
    ):
        continue

    text = read_text(path)

    if not text:
        continue

    text_cache[str(path)] = text

    score, reasons = doctrine_score(path, text)

    explicit_doctrine_marker = any(
        marker in text.lower()
        for marker in {
            "doctrine_id",
            "doctrine id",
            "doctrine_name",
            "doctrine name",
            "doctrine_version",
            "doctrine reference",
        }
    )

    if score < 10:
        continue

    if not path_signal and not explicit_doctrine_marker:
        continue

    metadata = parse_metadata(text)

    doctrine_id = normalize_identifier(
        metadata.get("doctrine_id")
    )

    doctrine_name = normalize_identifier(
        metadata.get("name")
    )

    version = normalize_identifier(
        metadata.get("version")
    )

    scope = normalize_identifier(
        metadata.get("scope")
    )

    owner = normalize_identifier(
        metadata.get("owner")
    )

    status = normalize_identifier(
        metadata.get("status")
    )

    priority = normalize_identifier(
        metadata.get("priority")
    )

    missing: list[str] = []

    if not doctrine_id:
        missing.append("DOCTRINE_ID")

    if not doctrine_name:
        missing.append("NAME")

    if not version:
        missing.append("VERSION")

    if not scope:
        missing.append("SCOPE")

    if not owner:
        missing.append("OWNER")

    if not status:
        missing.append("STATUS")

    text_lower = text.lower()

    has_rules = bool(
        re.search(
            r"\b(rules?|pravila|must|shall|forbidden|prohibition)\b",
            text_lower,
        )
    )

    has_prohibitions = bool(
        re.search(
            r"\b(forbidden|prohibition|deny|must not|ne smije)\b",
            text_lower,
        )
    )

    if not has_rules:
        missing.append("RULES")

    if not has_prohibitions:
        missing.append("PROHIBITIONS")

    classification = classify_initial(
        path,
        metadata,
        missing,
        score,
    )

    candidate_records.append(
        {
            "path": str(path),
            "sha256": record.get("sha256") or sha256_file(path),
            "size": size,
            "score": score,
            "discovery_reasons": reasons,
            "doctrine_id": doctrine_id,
            "name": doctrine_name,
            "version": version,
            "scope": scope,
            "owner": owner,
            "status_declared": status,
            "date": normalize_identifier(metadata.get("date")),
            "priority": priority,
            "has_rules": has_rules,
            "has_prohibitions": has_prohibitions,
            "missing_required_fields": missing,
            "classification": classification,
            "evidence_generated_path": any(
                term in path_lower
                for term in EVIDENCE_TERMS
            ),
        }
    )

id_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

for doctrine in candidate_records:
    doctrine_id = doctrine.get("doctrine_id")

    if doctrine_id:
        id_groups[doctrine_id].append(doctrine)

conflicts: list[dict[str, Any]] = []

for doctrine_id, group in sorted(id_groups.items()):
    hashes = sorted(
        {
            doctrine["sha256"]
            for doctrine in group
        }
    )

    versions = sorted(
        {
            doctrine["version"]
            for doctrine in group
            if doctrine.get("version")
        }
    )

    if len(hashes) > 1:
        conflicts.append(
            {
                "doctrine_id": doctrine_id,
                "paths": sorted(
                    doctrine["path"]
                    for doctrine in group
                ),
                "sha256_values": hashes,
                "versions": versions,
                "reason": "SAME_DOCTRINE_ID_DIFFERENT_CONTENT",
            }
        )

        for doctrine in group:
            doctrine["classification"] = "CONFLICT"

doctrine_text_by_path = {
    doctrine["path"]: text_cache.get(
        doctrine["path"],
        read_text(Path(doctrine["path"])),
    )
    for doctrine in candidate_records
}

config_candidates = [
    record
    for record in inventory
    if (
        record.get("type") == "FILE"
        and Path(record.get("path", "")).suffix.lower()
        in CONFIG_SUFFIXES
        and int(record.get("size") or 0) <= 2 * 1024 * 1024
    )
]

validator_candidates = [
    record
    for record in inventory
    if (
        record.get("type") == "FILE"
        and any(
            term in str(record.get("path", "")).lower()
            for term in VALIDATOR_TERMS
        )
    )
]

output_candidates = [
    record
    for record in inventory
    if (
        record.get("type") == "FILE"
        and any(
            term in str(record.get("path", "")).lower()
            for term in OUTPUT_TERMS
        )
    )
]

agent_map: list[dict[str, Any]] = []
linked_doctrine_paths: set[str] = set()

for agent in canonical_agents:
    class_name = str(agent.get("class_name") or "")
    role = str(agent.get("role") or "")
    agent_id = normalize_identifier(agent.get("agent_id"))
    explicit_doctrine = normalize_identifier(
        agent.get("doctrine_reference")
    )

    terms = tokenise(class_name) | tokenise(role)

    exact_values = [
        value
        for value in {
            class_name,
            role,
            agent_id or "",
        }
        if value
    ]

    doctrine_matches: list[dict[str, Any]] = []

    for doctrine in candidate_records:
        text = doctrine_text_by_path.get(
            doctrine["path"],
            "",
        )

        match_score = relevance_score(
            doctrine["path"],
            text,
            terms,
            exact_values,
        )

        if explicit_doctrine:
            if (
                explicit_doctrine.lower()
                == str(doctrine.get("doctrine_id") or "").lower()
            ):
                match_score += 50

            if explicit_doctrine.lower() in text.lower():
                match_score += 30

        if match_score > 0:
            doctrine_matches.append(
                {
                    "path": doctrine["path"],
                    "doctrine_id": doctrine.get("doctrine_id"),
                    "classification": doctrine["classification"],
                    "sha256": doctrine["sha256"],
                    "match_score": match_score,
                    "link_type": (
                        "EXPLICIT"
                        if explicit_doctrine
                        and (
                            explicit_doctrine.lower()
                            == str(
                                doctrine.get("doctrine_id") or ""
                            ).lower()
                            or explicit_doctrine.lower()
                            in text.lower()
                        )
                        else "INFERRED"
                    ),
                }
            )

    doctrine_matches.sort(
        key=lambda item: (
            -item["match_score"],
            item["path"],
        )
    )

    doctrine_matches = doctrine_matches[:10]

    for match in doctrine_matches:
        linked_doctrine_paths.add(match["path"])

    config_matches: list[dict[str, Any]] = []

    for record in config_candidates:
        path = str(record.get("path", ""))
        text = text_cache.get(path)

        if text is None:
            text = read_text(Path(path), 1048576)
            text_cache[path] = text

        score = relevance_score(
            path,
            text,
            terms,
            exact_values,
        )

        if score > 0:
            config_matches.append(
                {
                    "path": path,
                    "sha256": record.get("sha256"),
                    "match_score": score,
                }
            )

    config_matches.sort(
        key=lambda item: (
            -item["match_score"],
            item["path"],
        )
    )

    validator_matches: list[dict[str, Any]] = []

    for record in validator_candidates:
        path = str(record.get("path", ""))
        score = relevance_score(
            path,
            "",
            terms,
            exact_values,
        )

        if score > 0:
            validator_matches.append(
                {
                    "path": path,
                    "sha256": record.get("sha256"),
                    "match_score": score,
                }
            )

    validator_matches.sort(
        key=lambda item: (
            -item["match_score"],
            item["path"],
        )
    )

    output_matches: list[dict[str, Any]] = []

    for record in output_candidates:
        path = str(record.get("path", ""))
        score = relevance_score(
            path,
            "",
            terms,
            exact_values,
        )

        if score > 0:
            output_matches.append(
                {
                    "path": path,
                    "sha256": record.get("sha256"),
                    "match_score": score,
                }
            )

    output_matches.sort(
        key=lambda item: (
            -item["match_score"],
            item["path"],
        )
    )

    explicit_found = any(
        match["link_type"] == "EXPLICIT"
        for match in doctrine_matches
    )

    if explicit_doctrine and explicit_found:
        doctrine_link_status = "EXPLICIT_LINK_PASS"
    elif explicit_doctrine and not explicit_found:
        doctrine_link_status = "EXPLICIT_REFERENCE_NOT_FOUND"
    elif doctrine_matches:
        doctrine_link_status = "INFERRED_ONLY"
    else:
        doctrine_link_status = "NO_DOCTRINE_MATCH"

    agent_map.append(
        {
            "class_name": class_name,
            "role": role,
            "agent_id": agent_id,
            "module_sha256": agent.get("module_sha256"),
            "explicit_doctrine_reference": explicit_doctrine,
            "doctrine_link_status": doctrine_link_status,
            "doctrine_matches": doctrine_matches,
            "config_matches": config_matches[:5],
            "validator_matches": validator_matches[:5],
            "output_matches": output_matches[:5],
        }
    )

agents_without_explicit_doctrine = [
    item["class_name"]
    for item in agent_map
    if item["doctrine_link_status"] != "EXPLICIT_LINK_PASS"
]

agents_without_any_doctrine_match = [
    item["class_name"]
    for item in agent_map
    if item["doctrine_link_status"] == "NO_DOCTRINE_MATCH"
]

unlinked_doctrines = [
    {
        "path": doctrine["path"],
        "doctrine_id": doctrine.get("doctrine_id"),
        "classification": doctrine["classification"],
        "sha256": doctrine["sha256"],
    }
    for doctrine in candidate_records
    if doctrine["path"] not in linked_doctrine_paths
]

classification_counts = Counter(
    doctrine["classification"]
    for doctrine in candidate_records
)

incomplete_doctrines = [
    doctrine
    for doctrine in candidate_records
    if doctrine["classification"] == "INCOMPLETE"
]

active_doctrines = [
    doctrine
    for doctrine in candidate_records
    if doctrine["classification"] == "ACTIVE"
]

canonical_candidates = [
    doctrine
    for doctrine in candidate_records
    if doctrine["classification"] == "CANONICAL_CANDIDATE"
]

if not candidate_records:
    final_status = "FAIL"
elif conflicts or agents_without_explicit_doctrine or incomplete_doctrines:
    final_status = "PASS_WITH_FINDINGS"
else:
    final_status = "PASS"

doctrine_report = {
    "protocol": 888,
    "batch": "BATCH_03_DOCTRINE_DISCOVERY_AND_MAPPING",
    "doctrines": sorted(
        candidate_records,
        key=lambda item: (
            item["classification"],
            item["doctrine_id"] or "",
            item["path"],
        ),
    ),
}

mapping_report = {
    "agent_doctrine_config_validator_output_map": agent_map,
    "agents_without_explicit_doctrine": (
        agents_without_explicit_doctrine
    ),
    "agents_without_any_doctrine_match": (
        agents_without_any_doctrine_match
    ),
    "unlinked_doctrines": unlinked_doctrines,
    "conflicts": conflicts,
}

summary = {
    "protocol": 888,
    "batch": "BATCH_03_DOCTRINE_DISCOVERY_AND_MAPPING",
    "status": final_status,
    "strict_doctrine_candidate_count": len(candidate_records),
    "classification_counts": dict(
        sorted(classification_counts.items())
    ),
    "active_doctrines": len(active_doctrines),
    "canonical_candidate_doctrines": len(canonical_candidates),
    "incomplete_doctrines": len(incomplete_doctrines),
    "conflict_groups": len(conflicts),
    "agents_mapped": len(agent_map),
    "agents_with_explicit_doctrine": (
        len(agent_map) - len(agents_without_explicit_doctrine)
    ),
    "agents_without_explicit_doctrine": (
        agents_without_explicit_doctrine
    ),
    "agents_without_any_doctrine_match": (
        agents_without_any_doctrine_match
    ),
    "unlinked_doctrines": len(unlinked_doctrines),
    "files_deleted": 0,
    "original_files_modified": 0,
    "unknown_scripts_executed": 0,
}

doctrine_path = EVIDENCE / "DOCTRINE_REGISTRY_CANDIDATES.json"
mapping_path = EVIDENCE / "AGENT_DOCTRINE_MAP.json"
conflict_path = EVIDENCE / "DOCTRINE_CONFLICTS.json"
summary_path = EVIDENCE / "BATCH_03_SUMMARY.json"

doctrine_path.write_text(
    json.dumps(
        doctrine_report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

mapping_path.write_text(
    json.dumps(
        mapping_report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

conflict_path.write_text(
    json.dumps(
        conflicts,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

summary_path.write_text(
    json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

manifest_entries: list[str] = []

for path in sorted(EVIDENCE.iterdir()):
    if (
        path.is_file()
        and path.name != "EVIDENCE_MANIFEST.sha256"
    ):
        manifest_entries.append(
            f"{sha256_file(path)}  {path.name}"
        )

manifest_path = EVIDENCE / "EVIDENCE_MANIFEST.sha256"
manifest_path.write_text(
    "\n".join(manifest_entries) + "\n",
    encoding="utf-8",
)

print("PROTOCOL=888")
print("BATCH=BATCH_03_DOCTRINE_DISCOVERY_AND_MAPPING")
print(f"STATUS={final_status}")
print(f"EVIDENCE_FOLDER={EVIDENCE}")
print(
    "STRICT_DOCTRINE_CANDIDATES="
    f"{len(candidate_records)}"
)
print(f"ACTIVE_DOCTRINES={len(active_doctrines)}")
print(
    "CANONICAL_CANDIDATE_DOCTRINES="
    f"{len(canonical_candidates)}"
)
print(f"INCOMPLETE_DOCTRINES={len(incomplete_doctrines)}")
print(f"DOCTRINE_CONFLICT_GROUPS={len(conflicts)}")
print(f"AGENTS_MAPPED={len(agent_map)}")
print(
    "AGENTS_WITH_EXPLICIT_DOCTRINE="
    f"{len(agent_map) - len(agents_without_explicit_doctrine)}"
)
print(
    "AGENTS_WITHOUT_EXPLICIT_DOCTRINE="
    f"{len(agents_without_explicit_doctrine)}"
)
print(
    "AGENTS_WITHOUT_ANY_DOCTRINE_MATCH="
    f"{len(agents_without_any_doctrine_match)}"
)
print(f"UNLINKED_DOCTRINES={len(unlinked_doctrines)}")

for classification, count in sorted(
    classification_counts.items()
):
    print(
        f"DOCTRINE_CLASS_{classification}={count}"
    )

for index, item in enumerate(agent_map, 1):
    top_doctrine = (
        item["doctrine_matches"][0]
        if item["doctrine_matches"]
        else None
    )

    print(
        f"AGENT_MAP_{index:02d}="
        f"{item['class_name']}|"
        f"ROLE={item['role']}|"
        f"LINK_STATUS={item['doctrine_link_status']}|"
        f"TOP_DOCTRINE_ID="
        f"{top_doctrine.get('doctrine_id') if top_doctrine else 'NONE'}|"
        f"TOP_DOCTRINE_CLASS="
        f"{top_doctrine.get('classification') if top_doctrine else 'NONE'}|"
        f"DOCTRINE_MATCHES={len(item['doctrine_matches'])}|"
        f"CONFIG_MATCHES={len(item['config_matches'])}|"
        f"VALIDATOR_MATCHES={len(item['validator_matches'])}|"
        f"OUTPUT_MATCHES={len(item['output_matches'])}"
    )

print(f"DOCTRINE_REPORT_SHA256={sha256_file(doctrine_path)}")
print(f"MAPPING_REPORT_SHA256={sha256_file(mapping_path)}")
print(f"CONFLICT_REPORT_SHA256={sha256_file(conflict_path)}")
print(f"SUMMARY_SHA256={sha256_file(summary_path)}")
print(f"EVIDENCE_MANIFEST_SHA256={sha256_file(manifest_path)}")
print("FILES_DELETED=0")
print("ORIGINAL_FILES_MODIFIED=0")
print("UNKNOWN_SCRIPTS_EXECUTED=0")
print("NEXT_REQUIRED=BATCH_04_STATIC_VALIDATION")
