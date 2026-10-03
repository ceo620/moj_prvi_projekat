# TITAN_FORENSIC_CONTEXT_EXTRACTION_RAG_READY

## 0. META

```json
{
  "document_type": "forensic_context_extraction",
  "purpose": "RAG_pipeline_migration",
  "scope": "available_conversation_context_and_TITAN_memory",
  "date": "2026-05-06",
  "status": "CONTROLLED_DOSSIER_REVIEW_READY",
  "system_mode": "SYSTEM_RED_REPORT_ONLY",
  "validation_policy": "No validation claim without manifest, hash, log and evidence pack"
}
```

## 1. FINANSIJSKA MATRICA

```json
{
  "active_capex": {
    "amount_eur": 43500000,
    "phase": "Phase 102",
    "protocol": "RUNHARVEST2",
    "status": "ACTIVE_CANONICAL_PARAMETER"
  },
  "legacy_capex_anchor": {
    "amount_eur": 19900000,
    "site": "Tuzi",
    "operational_start": "January 2027",
    "status": "LEGACY_OR_SCRIPT_SPECIFIC_UNTIL_RECONCILED",
    "risk": "Conflict with active EUR 43.5M Phase 102 CAPEX"
  },
  "historical_capex_fragments": [
    {
      "code": "LOG-001",
      "description": "Logistics",
      "amount_eur": 14088000,
      "percentage": "19.90%",
      "implied_total_context": "approx. EUR 70.2M",
      "status": "HISTORICAL_MODEL_FRAGMENT_NOT_ACTIVE_CANON"
    },
    {
      "code": "CIVIL-001",
      "description": "Civil Works",
      "amount_eur": 17900000,
      "percentage": "28.50%",
      "status": "HISTORICAL_MODEL_FRAGMENT_NOT_ACTIVE_CANON"
    }
  ],
  "opex": {
    "locked_numeric_values": [],
    "status": "NO_FINAL_NUMERIC_OPEX_ASSUMPTIONS_LOCKED",
    "required_fields": [
      "energy_cost",
      "labor_cost",
      "maintenance_cost",
      "insurance_cost",
      "logistics_opex",
      "quality_control_cost",
      "environmental_monitoring_cost",
      "IT_and_RAG_operations_cost",
      "administration_cost",
      "working_capital_requirement"
    ]
  },
  "step103": {
    "current_phase": "Phase 102",
    "next_phase_candidate": "STEP103",
    "status": "NOT_FULLY_DEFINED",
    "hard_gate": "No STEP103 lock without CAPEX reconciliation and evidence manifest",
    "required_actions": [
      "Reconcile EUR 43.5M vs EUR 19.9M",
      "Freeze CAPEX bridge table",
      "Create DSCR / IRR / NPV / WACC matrix",
      "Create OPEX schedule",
      "Attach evidence pack, manifest and hashes"
    ]
  },
  "required_financial_indicators": [
    "CAPEX",
    "OPEX",
    "NPV",
    "IRR",
    "WACC",
    "DSCR",
    "EBITDA",
    "debt_service",
    "loan_amount",
    "loan_tenor",
    "interest_rate",
    "grace_period",
    "covenants",
    "default_events",
    "working_capital",
    "subsidy",
    "grant",
    "state_aid",
    "sovereign_support"
  ]
}
```

## 2. OPERATIVNI PARAMETRI

```json
{
  "locations": {
    "country": "Montenegro",
    "city_context": "Podgorica",
    "project_site": "Tuzi",
    "company": "ARS Metal Industries DOO",
    "desktop_paths_seen": [
      "C:\\Users\\Korisnik\\Desktop",
      "C:\\Users\\Lenovo\\Desktop"
    ]
  },
  "oee": {
    "target_percent": 85,
    "status": "USER_SPECIFIED_TARGET",
    "required_breakdown": [
      "availability",
      "performance",
      "quality"
    ]
  },
  "transformer_domain": {
    "products": [
      "power transformers",
      "distribution transformers",
      "oil-immersed transformers",
      "eco transformers",
      "high-voltage transformer tanks",
      "transformer tank project",
      "Tiran power transformer project",
      "Eco transformer takeover / expansion"
    ],
    "voltage_terms": [
      "110 kV",
      "220 kV",
      "400 kV"
    ],
    "utility_entities": [
      "CGES",
      "CEDIS",
      "EPCG"
    ],
    "eco_transformer_datasheet_fields_required": [
      "loss_class",
      "noise_level",
      "oil_type_or_biodegradable_insulating_fluid",
      "efficiency_standard",
      "cooling_method",
      "rated_power",
      "rated_voltage",
      "short_circuit_impedance",
      "insulation_class",
      "temperature_rise",
      "testing_protocol",
      "IEC_compliance",
      "environmental_compliance"
    ],
    "status": "DOMAIN_CONTEXT_PRESENT_BUT_FINAL_TECHNICAL_DATASHEET_NOT_LOCKED"
  }
}
```

## 3. INSTITUCIONALNI KREDITORI

```json
{
  "target_institutions": [
    "European Investment Bank (EIB)",
    "European Bank for Reconstruction and Development (EBRD)"
  ],
  "submission_orientation": [
    "bank-ready style",
    "institutional-grade reporting",
    "evidence-linked documentation",
    "sovereign / government project readability",
    "PPP / JPP compatibility",
    "IFRS-aligned financial presentation"
  ],
  "approval_status": {
    "EIB": "NOT_ACCEPTED_OR_APPROVED_IN_CONTEXT",
    "EBRD": "NOT_ACCEPTED_OR_APPROVED_IN_CONTEXT"
  },
  "forbidden_claims_without_evidence": [
    "EIB accepted",
    "EBRD accepted",
    "bank approved",
    "sovereign-grade validated",
    "100% validated",
    "risk-free"
  ],
  "allowed_claims": [
    "submission-oriented",
    "review-ready",
    "controlled dossier",
    "audit-prepared",
    "evidence-linked",
    "subject to final legal, technical and financial validation"
  ],
  "ebrd_pr_1_10": [
    {"pr": "PR1", "title": "Assessment and Management of Environmental and Social Impacts and Issues", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR2", "title": "Labour and Working Conditions", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR3", "title": "Resource Efficiency and Pollution Prevention and Control", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR4", "title": "Health, Safety and Security", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR5", "title": "Land Acquisition, Restrictions on Land Use and Involuntary Resettlement", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR6", "title": "Biodiversity Conservation and Sustainable Management of Living Natural Resources", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR7", "title": "Indigenous Peoples", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR8", "title": "Cultural Heritage", "status": "EVIDENCE_REQUIRED"},
    {"pr": "PR9", "title": "Financial Intermediaries", "status": "CONDITIONAL_EVIDENCE_REQUIRED"},
    {"pr": "PR10", "title": "Information Disclosure and Stakeholder Engagement", "status": "EVIDENCE_REQUIRED"}
  ],
  "ppp_jpp_required_blocks": [
    "public-private partnership rationale",
    "public interest statement",
    "government procurement cycle mapping",
    "fiscal obligation review",
    "state aid / subsidy review",
    "sovereign guarantee review if applicable",
    "municipality / ministry approval chain",
    "land and permitting review",
    "concession / license analysis if applicable",
    "environmental permitting",
    "grid operator interface"
  ]
}
```

## 4. KRIPTOGRAFSKI LANAC

```json
{
  "known_hashes": [
    {
      "file_name": "TITAN_DEEP_HARVEST_V4.ps1",
      "sha256": "2108e104e46e7d4f06b3f54c1efae2062b0e8f654e0b572004cb6fc643ee075d",
      "target_path": "C:\\Users\\Korisnik\\Desktop\\02_BACKUP_ARCHIVES",
      "status": "FORENSICALLY_INSPECTED_NOT_AUDIT_APPROVED",
      "issues": [
        "no input hashing",
        "no manifest",
        "no gap register",
        "silent catch block",
        "weak extraction for PDF/XLSX/DOCX via Get-Content",
        "misleading GO - AUTHORIZED text inconsistent with SYSTEM RED / REPORT_ONLY doctrine"
      ]
    }
  ],
  "hash_policy": {
    "minimum": "SHA-256",
    "optional_stronger": "SHA3-512",
    "package_hash_required": true,
    "merkle_root_recommended": true,
    "no_validation_without_hash_manifest": true
  },
  "known_file_ids": [
    "11932_RUN_COVENANT_V2_RESCAN_ALL",
    "11933_RUN_GHOST_PROTOCOL_V2_RESTORE",
    "11934_RUN_HYPER_V2_RESCAN",
    "11935_RUN_MEDIA_EXPORT_TO_NEW_DISK_STEP61",
    "11936_RUN_SCANNER_V2",
    "11937_RUN_SCANNER_V2_DEBUG",
    "11938_RUN_TITAN_8X_IMPERVIOUS_CONTROL_SYSTEM_STEP93",
    "11939_RUN_TITAN_FULL_RAG_DRY_RUN",
    "11940_RUN_TITAN_FULL_RAG_EXECUTE_SMALL"
  ],
  "manifest_required_fields": [
    "file_path",
    "file_name",
    "file_size_bytes",
    "sha256",
    "modified_time",
    "scan_time",
    "extension",
    "mime_or_magic_bytes",
    "status",
    "risk_flags",
    "error_message",
    "source_folder",
    "output_manifest_id"
  ]
}
```

## 5. KANONSKE SKRIPTE

```json
{
  "canonical_scripts": {
    "bootstrap_and_config": [
      "00_SETUP_STRUCTURE.py",
      "00_CREATE_TITAN_DESKTOP_STRUCTURE.ps1",
      "01_config_init.py"
    ],
    "database": [
      "02_DATABASE_INIT.py"
    ],
    "ingestion_and_queue": [
      "01_TITAN_ELITE_RECONSTRUCTOR.py",
      "03_v31_producer.py",
      "03_v29_queue_consumer.py"
    ],
    "kernel_runtime": [
      "06_kernel_live_mode_v1_1.py",
      "06_kernel_live_mode_daemon.py",
      "07_status_monitor_v1.py"
    ],
    "sync_and_ssot": [
      "04_ssot_generator.py",
      "08_sync_sqlite_to_existing_control_tower.py",
      "09_document_register_builder.py"
    ],
    "packaging_and_audit": [
      "11_export_packager.py",
      "12_backup_snapshot.py",
      "13_audit_manifest_builder.py"
    ],
    "decision_and_signals": [
      "05_kernel_decision_engine.py",
      "14_check_document_signals.py"
    ],
    "forensic_engines": [
      "TITAN_FORENSIC_ENGINE_v3_3_FORENSIC_FINAL.py",
      "TITAN_FORENSIC_ENGINE_v3_4_AUDIT_LOCKED.py",
      "TITAN_FORENSIC_ENGINE_v3_5_ENTERPRISE_LOCKED.py"
    ],
    "powershell_orchestrators": [
      "TITAN_RECOVERY_ORCHESTRATOR_v6.ps1",
      "TITAN_MASTER_CONTROL_TOWER_v7.ps1",
      "TITAN_EXECUTIVE_MORNING_CONSOLE_v8.ps1",
      "TITAN_FINAL_HARMONIZED_CONTROL_v9.ps1",
      "OPERACIJA_REGISTRATOR_v2_PRINT_READY.ps1"
    ]
  }
}
```

## 6. OPERATIVNE PUTANJE

```json
{
  "paths": {
    "working_export": "C:\\Users\\Korisnik\\Desktop\\TITAN_WORKING_FILES_EXPORT_888",
    "logs": "C:\\Users\\Korisnik\\Desktop\\TITAN_WORKING_FILES_EXPORT_888\\07_LOGS_CHECKPOINTS",
    "manifests_hashes": "C:\\Users\\Korisnik\\Desktop\\TITAN_WORKING_FILES_EXPORT_888\\06_MANIFESTS_HASHES",
    "backup_archives": "C:\\Users\\Korisnik\\Desktop\\02_BACKUP_ARCHIVES",
    "purge_recovery": "C:\\Users\\Korisnik\\Desktop\\02_BACKUP_ARCHIVES\\DESKTOP_PURGE_20260505",
    "registrar": "C:\\Users\\Korisnik\\Desktop\\OPERACIJA_REGISTRATOR",
    "rag": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG",
    "rag_recovery": "C:\\Users\\Korisnik\\Desktop\\02_BACKUP_ARCHIVES\\DESKTOP_PURGE_20260505\\TITAN_FULL_RAG",
    "kernel_scripts_legacy": "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS",
    "queue_legacy": "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS\\00_QUEUE\\queue.jsonl",
    "sqlite_state_legacy": "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS\\03_ORCHESTRATION\\v29_state.db",
    "control_tower_legacy": "C:\\Users\\Lenovo\\Desktop\\TITAN_GRID\\00_SYSTEM\\00_CONTROL_TOWER\\Control_Tower.xlsx",
    "document_register_legacy": "C:\\Users\\Lenovo\\Desktop\\TITAN_GRID\\01_VDR_GOVERNANCE\\01_MASTER_INDEX\\Document_Register.xlsx",
    "golden_vault": "C:\\Users\\Korisnik\\Desktop\\ARS_METAL_GOLDEN_VAULT"
  }
}
```

## 7. SISTEMSKA DOKTRINA

```json
{
  "doctrine": [
    "Evidence precedes intelligence",
    "Retrieval precedes generation",
    "Audit precedes decision",
    "No claim without traceable source",
    "No validation without manifest, hash, log and evidence pack",
    "SSoT is the authority layer; narrative is downstream"
  ],
  "statuses": {
    "SYSTEM_RED": "Restricted execution mode; no destructive operations",
    "REPORT_ONLY": "Script may generate reports but may not alter source files",
    "CONTROLLED_WRITE_SNAPSHOT": "Script may write new controlled artifacts to output folder without modifying originals",
    "LOCKED": "Working version frozen as current reference",
    "AUDIT_LOCKED": "Frozen for audit; changes require new version"
  }
}
```

## 8. RAG PIPELINE

```json
{
  "rag_pipeline": [
    "01_discover_files.py",
    "02_safety_filter.py",
    "03_extract_text.py",
    "04_chunk_text.py",
    "05_build_embeddings.py",
    "06_search_rag.py",
    "07_generate_answer.py",
    "08_write_audit_log.py",
    "09_incremental_refresh.py",
    "10_morning_briefing.py",
    "11_query_console.py",
    "12_evidence_pack_reporter.py",
    "13_source_citation_verifier.py",
    "14_conflict_detector.py",
    "15_ssot_candidate_extractor.py",
    "16_financial_signal_extractor.py",
    "17_risk_signal_extractor.py",
    "18_document_priority_ranker.py",
    "19_night_run_orchestrator.py",
    "20_rag_control_tower_export.py"
  ],
  "execution_modes": [
    "DRY_RUN",
    "EXECUTE_SMALL",
    "FULL_SCAN_AFTER_RECOVERY_AND_MANIFEST_VALIDATION"
  ]
}
```

## 9. FINAL MIGRATION OBJECT

```json
{
  "canonical_phase": "Phase 102",
  "next_phase": "STEP103",
  "active_capex_eur": 43500000,
  "legacy_capex_eur": 19900000,
  "project_site": "Tuzi, Montenegro",
  "company": "ARS Metal Industries DOO",
  "project_period": "2026-2028",
  "oee_target_percent": 85,
  "system_mode": "SYSTEM_RED_REPORT_ONLY",
  "ssot_status": "CONTROLLED_DOSSIER_REVIEW_READY",
  "hash_algorithm_minimum": "SHA-256",
  "known_sha256_count": 1,
  "primary_lenders_targeted": [
    "EIB",
    "EBRD"
  ],
  "validation_claim_allowed": false,
  "next_required_actions": [
    "CAPEX reconciliation EUR 43.5M vs EUR 19.9M",
    "OPEX matrix creation",
    "STEP103 gate definition",
    "EBRD PR1-10 evidence attachment",
    "Full hash manifest generation",
    "TITAN_DEEP_HARVEST_V4.ps1 remediation",
    "RAG DRY_RUN and EXECUTE_SMALL",
    "VDR register lock",
    "Control Tower sync",
    "Audit pack export"
  ]
}
```
