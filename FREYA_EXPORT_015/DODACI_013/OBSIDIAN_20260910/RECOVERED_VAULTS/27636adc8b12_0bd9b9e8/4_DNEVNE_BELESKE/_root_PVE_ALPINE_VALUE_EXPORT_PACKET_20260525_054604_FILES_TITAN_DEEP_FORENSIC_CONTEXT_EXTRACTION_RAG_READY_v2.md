# TITAN / TITAN-GRID — Deep Forensic Context Extraction v2

**Document Type:** RAG migration extract
**Scope:** visible conversation history + generated artifacts + active canon
**Generated UTC:** 2026-05-06T06:39:06+00:00
**Status:** SYSTEM RED — STEP102 LOCKED — NO FINAL USE

## FORENSIC BOUNDARY

```json
{
  "audit_boundary": "visible_chat_history_current_session_generated_artifacts_active_memory_context",
  "active_canon": {
    "system_status": "SYSTEM RED",
    "risk_baseline": 890,
    "p0_gates": "10/10 BLOCKED",
    "evidence_gaps_remaining": 6,
    "evidence_approved": 0,
    "gates_closed": 0,
    "step97_step101": "ACCEPTED / REVALIDATED",
    "step102": "LOCKED / NOT ACCEPTED",
    "step103": "NOT_OPEN_FOR_ACCEPTANCE_UNTIL_STEP102_BLOCKERS_CLOSED",
    "final_use_allowed": "NO",
    "ssot_write_allowed": "NO",
    "evidence_approval_allowed": "NO",
    "gate_closure_allowed": "NO"
  }
}
```

## 1. [FINANSIJSKA MATRICA]

```json
{
  "classification": "FINANSIJSKA_MATRICA",
  "active_canon": {
    "system_status": "SYSTEM RED",
    "risk_baseline": 890,
    "p0_gates": "10/10 BLOCKED",
    "evidence_gaps_remaining": 6,
    "evidence_approved": 0,
    "gates_closed": 0,
    "step97_step101": "ACCEPTED / REVALIDATED",
    "step102": "LOCKED / NOT ACCEPTED",
    "step103": "NOT_OPEN_FOR_ACCEPTANCE_UNTIL_STEP102_BLOCKERS_CLOSED",
    "final_use_allowed": "NO",
    "ssot_write_allowed": "NO",
    "evidence_approval_allowed": "NO",
    "gate_closure_allowed": "NO"
  },
  "phase_102": {
    "capex_eur": 43500000,
    "status": "LOCKED / NOT ACCEPTED",
    "treatment": "REVIEW_REQUIRED_FINANCIAL_ASSUMPTION",
    "final_use_allowed": "NO"
  },
  "step_103_transition": {
    "status": "REFERENCED / NOT OPEN FOR ACCEPTANCE",
    "transition_rule": "STEP103 cannot be accepted until STEP102 blockers, evidence gaps, P0 gates and audit gates are closed.",
    "final_use_allowed": "NO"
  },
  "values": [
    {
      "parameter": "TOTAL_PROJECT_CAPEX",
      "value": 43500000,
      "currency": "EUR",
      "source_context": "user prompt and v60.5 OMEGA Word COM table",
      "status": "INTERNAL_DRAFT_LOCKED_VALUE_NOT_ACCEPTED",
      "final_use_allowed": "NO"
    },
    {
      "parameter": "MIA_NON_DILUTIVE_GRANT",
      "value": 10200000,
      "currency": "EUR",
      "source_context": "v60.5 OMEGA Word COM table",
      "status": "UNVERIFIED_REFERENCE",
      "final_use_allowed": "NO"
    },
    {
      "parameter": "ASSET_BACKED_COLLATERAL",
      "value": 22000000,
      "currency": "EUR",
      "source_context": "v60.5 OMEGA Word COM table",
      "status": "UNVERIFIED_REFERENCE",
      "final_use_allowed": "NO"
    },
    {
      "parameter": "INSTITUTIONAL_DSCR",
      "value": "1.38x",
      "currency": "N/A",
      "source_context": "v60.5 OMEGA Word COM table",
      "status": "UNVERIFIED_REFERENCE",
      "final_use_allowed": "NO"
    },
    {
      "parameter": "HISTORICAL_SOVEREIGN_ANCHOR_CAPEX",
      "value": 19900000,
      "currency": "EUR",
      "source_context": "older TITAN GRID/TITAN 11 anchor",
      "status": "HISTORICAL_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "parameter": "HISTORICAL_CAPEX_MASTER_LOGISTICS",
      "value": 14088000,
      "currency": "EUR",
      "source_context": "older CAPEX_Master memory snippet",
      "status": "HISTORICAL_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "parameter": "HISTORICAL_CAPEX_MASTER_CIVIL_WORKS",
      "value": 17900000,
      "currency": "EUR",
      "source_context": "older CAPEX_Master memory snippet",
      "status": "HISTORICAL_ONLY",
      "final_use_allowed": "NO"
    }
  ],
  "opex": {
    "status": "UNKNOWN / MISSING_EVIDENCE",
    "required_fields": [
      "fixed OPEX",
      "variable OPEX",
      "personnel cost",
      "energy cost",
      "maintenance cost",
      "insurance",
      "IT/OT cost"
    ],
    "final_use_allowed": "NO"
  },
  "required_financial_model_inputs": [
    "CAPEX breakdown",
    "OPEX base case",
    "revenue model",
    "OEE assumptions",
    "debt/equity/grant split",
    "loan tenor",
    "interest rate",
    "repayment schedule",
    "WACC",
    "IRR",
    "NPV",
    "DSCR",
    "sensitivity cases",
    "collateral valuation"
  ]
}
```

## 2. [OPERATIVNI PARAMETRI]

```json
{
  "classification": "OPERATIVNI_PARAMETRI",
  "active_canon": {
    "system_status": "SYSTEM RED",
    "risk_baseline": 890,
    "p0_gates": "10/10 BLOCKED",
    "evidence_gaps_remaining": 6,
    "evidence_approved": 0,
    "gates_closed": 0,
    "step97_step101": "ACCEPTED / REVALIDATED",
    "step102": "LOCKED / NOT ACCEPTED",
    "step103": "NOT_OPEN_FOR_ACCEPTANCE_UNTIL_STEP102_BLOCKERS_CLOSED",
    "final_use_allowed": "NO",
    "ssot_write_allowed": "NO",
    "evidence_approval_allowed": "NO",
    "gate_closure_allowed": "NO"
  },
  "oee": {
    "target_percent": 85,
    "status": "REVIEW_REQUIRED_TECHNICAL_PARAMETER",
    "final_use_allowed": "NO"
  },
  "locations": [
    {
      "location": "Tuzi",
      "role": "TITAN-GRID / industrial platform location reference",
      "status": "CANONICAL_REFERENCE_ONLY_BUT_SITE_EVIDENCE_REQUIRED",
      "final_use_allowed": "NO"
    },
    {
      "location": "Podgorica",
      "role": "regional/admin context",
      "status": "UNVERIFIED_REFERENCE",
      "final_use_allowed": "NO"
    },
    {
      "location": "Ars Metal Industries",
      "role": "industrial/corporate context",
      "status": "UNVERIFIED_REFERENCE",
      "final_use_allowed": "NO"
    }
  ],
  "transformer_scope": {
    "product_domain": [
      "ecological transformers",
      "oil-immersed transformers",
      "distribution transformers",
      "power transformers",
      "transformer tanks"
    ],
    "known_context": [
      "Tiran power transformer project",
      "Titan 1 transformer tank project",
      "Eco transformer takeover/expansion",
      "110/220/400 kV historical context"
    ],
    "missing_specs": [
      "rated power",
      "voltage class",
      "loss class",
      "cooling method",
      "insulating liquid",
      "IEC/EN standards",
      "annual capacity",
      "test bay",
      "BOM"
    ],
    "final_use_allowed": "NO"
  },
  "digital_stack": {
    "systems": [
      "TITAN MASTER SSOT v1.0",
      "TITAN_FULL_RAG",
      "TITAN_KERNEL_SCRIPTS",
      "Control Tower",
      "Kernel to Full RAG Bridge"
    ],
    "signal_count_claim": 3756,
    "signal_count_status": "UNVERIFIED_REFERENCE",
    "final_use_allowed": "NO"
  }
}
```

## 3. [INSTITUCIONALNI KREDITORI]

```json
{
  "classification": "INSTITUCIONALNI_KREDITORI",
  "active_canon": {
    "system_status": "SYSTEM RED",
    "risk_baseline": 890,
    "p0_gates": "10/10 BLOCKED",
    "evidence_gaps_remaining": 6,
    "evidence_approved": 0,
    "gates_closed": 0,
    "step97_step101": "ACCEPTED / REVALIDATED",
    "step102": "LOCKED / NOT ACCEPTED",
    "step103": "NOT_OPEN_FOR_ACCEPTANCE_UNTIL_STEP102_BLOCKERS_CLOSED",
    "final_use_allowed": "NO",
    "ssot_write_allowed": "NO",
    "evidence_approval_allowed": "NO",
    "gate_closure_allowed": "NO"
  },
  "institutions": [
    {
      "institution": "EIB",
      "role": "institutional lender / submission-readiness reference",
      "status": "REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "institution": "EBRD",
      "role": "institutional lender / PR1-10 reference",
      "status": "REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "institution": "IFC",
      "role": "profile supported by scripts but not evidenced as active creditor",
      "status": "UNVERIFIED_REFERENCE",
      "final_use_allowed": "NO"
    }
  ],
  "ebrd_pr_1_10": [
    [
      "PR1",
      "Assessment and management of E&S risks and impacts",
      "25_esg_permitting_risk_analyzer; ESG checklist; risk register",
      "ESIA/EIA, ESMS, impact assessment",
      "REVIEW_REQUIRED"
    ],
    [
      "PR2",
      "Labour and working conditions",
      "ESG/legal gap register",
      "HR policy, labour compliance, OHS records",
      "MISSING_EVIDENCE"
    ],
    [
      "PR3",
      "Resource efficiency and pollution prevention/control",
      "ESG KPI; ecological transformer claim review",
      "resource efficiency, emissions, waste and pollution controls",
      "MISSING_EVIDENCE"
    ],
    [
      "PR4",
      "Health, safety and security",
      "Risk register; ESG/EHS controls",
      "OHS plan, emergency response, security plan",
      "MISSING_EVIDENCE"
    ],
    [
      "PR5",
      "Land acquisition, restrictions and involuntary resettlement",
      "Legal compliance gap analyzer",
      "land title, acquisition records, resettlement screening",
      "MISSING_EVIDENCE"
    ],
    [
      "PR6",
      "Biodiversity conservation",
      "ESG/permitting analyzer",
      "biodiversity screening and site environmental evidence",
      "MISSING_EVIDENCE"
    ],
    [
      "PR7",
      "Indigenous peoples",
      "Legal/ESG applicability screening",
      "applicability screening",
      "MISSING_EVIDENCE"
    ],
    [
      "PR8",
      "Cultural heritage",
      "Legal/ESG screening",
      "cultural heritage screening",
      "MISSING_EVIDENCE"
    ],
    [
      "PR9",
      "Financial intermediaries",
      "Lender DD pack if FI structure applies",
      "FI applicability decision",
      "MISSING_EVIDENCE"
    ],
    [
      "PR10",
      "Information disclosure and stakeholder engagement",
      "Reporting/transparency framework; receipt register",
      "SEP, disclosure log, grievance mechanism",
      "MISSING_EVIDENCE"
    ]
  ],
  "lender_controls": [
    "DD pack is not lender approval",
    "bankability analyzer is not financial advice",
    "legal analyzer is not legal advice",
    "ESG analyzer is not ESG certification",
    "CFO/ADMIN role required for export-intent"
  ]
}
```

## 4. [KRIPTOGRAFSKI LANAC]

```json
{
  "classification": "KRIPTOGRAFSKI_LANAC",
  "active_canon": {
    "system_status": "SYSTEM RED",
    "risk_baseline": 890,
    "p0_gates": "10/10 BLOCKED",
    "evidence_gaps_remaining": 6,
    "evidence_approved": 0,
    "gates_closed": 0,
    "step97_step101": "ACCEPTED / REVALIDATED",
    "step102": "LOCKED / NOT ACCEPTED",
    "step103": "NOT_OPEN_FOR_ACCEPTANCE_UNTIL_STEP102_BLOCKERS_CLOSED",
    "final_use_allowed": "NO",
    "ssot_write_allowed": "NO",
    "evidence_approval_allowed": "NO",
    "gate_closure_allowed": "NO"
  },
  "titan_full_rag_canonical_scripts": [
    {
      "step": 1,
      "script": "01_discover_files.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 2,
      "script": "02_safety_filter.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 3,
      "script": "03_extract_text.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 4,
      "script": "04_chunk_text.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 5,
      "script": "05_build_embeddings.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 6,
      "script": "06_search_rag.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 7,
      "script": "07_generate_answer.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 8,
      "script": "08_write_audit_log.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 9,
      "script": "09_incremental_refresh.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 10,
      "script": "10_morning_briefing.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 11,
      "script": "11_query_console.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 12,
      "script": "12_evidence_pack_reporter.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 13,
      "script": "13_source_citation_verifier.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 14,
      "script": "14_conflict_detector.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 15,
      "script": "15_ssot_candidate_extractor.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 16,
      "script": "16_financial_signal_extractor.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 17,
      "script": "17_risk_signal_extractor.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 18,
      "script": "18_document_priority_ranker.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 19,
      "script": "19_night_run_orchestrator.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 20,
      "script": "20_rag_control_tower_export.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 21,
      "script": "21_executive_report_pack_builder.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 22,
      "script": "22_lender_due_diligence_pack_builder.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 23,
      "script": "23_board_decision_memo_builder.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 24,
      "script": "24_legal_compliance_gap_analyzer.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 25,
      "script": "25_esg_permitting_risk_analyzer.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 26,
      "script": "26_capex_loan_bankability_analyzer.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 27,
      "script": "27_investor_data_room_freeze_builder.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 28,
      "script": "28_distribution_readiness_gatekeeper.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 29,
      "script": "29_external_release_package_builder.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 30,
      "script": "30_post_release_audit_and_receipt_register.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 31,
      "script": "31_ssot_alignment_validator.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 32,
      "script": "32_sovereign_charter_v60_1_builder.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    },
    {
      "step": 33,
      "script": "33_kernel_to_full_rag_bridge_mapper.py",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\08_scripts",
      "final_use_allowed": "NO"
    }
  ],
  "legacy_kernel_scripts": [
    "06_kernel_live_mode_v1_1.py",
    "15_control_tower_forensic_sync.py",
    "07_status_monitor_v1.py",
    "16_titan_segmenter.py",
    "17_titan_contract_miner.py",
    "18_titan_excel_miner.py",
    "19_titan_mass_miner.py"
  ],
  "known_static_hashes_from_context": [
    {
      "file_name": "TITAN_DEEP_HARVEST_V4.ps1",
      "sha256": "2108e104e46e7d4f06b3f54c1efae2062b0e8f654e0b572004cb6fc643ee075d",
      "status": "NOT_AUDIT_APPROVED",
      "issues": [
        "no input hashing",
        "no manifest",
        "no gap register",
        "silent catch block",
        "weak PDF/XLSX/DOCX extraction via Get-Content",
        "misleading GO - AUTHORIZED text"
      ],
      "final_use_allowed": "NO"
    }
  ],
  "current_session_artifact_hashes": [
    {
      "artifact_id": "ART-001",
      "file_name": "01_discover_files_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 32388,
      "sha256": "193c42ae3348a04bc6afaeffcce879a3a9f6778002997b7ed5ebbb3ce3c28d65",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-002",
      "file_name": "02_safety_filter_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 25828,
      "sha256": "15912924cf2c4cf82e5d82eb6748934ab530ffd4d7481623d44313fca2f26d98",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-003",
      "file_name": "03_extract_text_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 25548,
      "sha256": "1a81e3dd60e969b4804c0c8df43596b777d539463cad69449c9d271fcd90ce62",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-004",
      "file_name": "04_chunk_text_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 28464,
      "sha256": "d796c9aa5fec4e8cdc0e60466b536f0914a7057d40fd74d72352b05b38c99c90",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-005",
      "file_name": "05_build_embeddings_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 25679,
      "sha256": "2916a337a88ff3d681bd70a367433f4b6c706ea16d9ace9d6cc157e9e2de675c",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-006",
      "file_name": "06_search_rag_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 33905,
      "sha256": "e652903a220f89acb93c94627f6d85dfaa1de05e1c416dcbe2767101d0e17921",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-007",
      "file_name": "07_generate_answer_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 25242,
      "sha256": "d607a21a8ac6ebdcb8f271cb8495feecb57652ef09aceb58e5eaa0cf727af6bc",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-008",
      "file_name": "08_write_audit_log_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 22937,
      "sha256": "a50f7e384108621ee4f2286801fb2147b06b66043f0a8f20eff2f19a1e91f12f",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-009",
      "file_name": "09_incremental_refresh_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 23743,
      "sha256": "12862d277f17ed5d63a0f384efc3cc0109ece6ba521fd9811e6b7572d635ee4b",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-010",
      "file_name": "10_morning_briefing_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 33077,
      "sha256": "2f04c860f8005f2d9de152e169ac098de64b57f9485745e5c32f5792d484ab86",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-011",
      "file_name": "11_query_console_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 28355,
      "sha256": "e3e61662d85513d1a01440e493ab1a2af49e0fb00f0c2af8fc7a32ca4bf80dd1",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-012",
      "file_name": "12_evidence_pack_reporter_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 25228,
      "sha256": "b18a67e34d07cf90b2db4afe38a2851756e235d87774de0cbaced50a8287751d",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-013",
      "file_name": "13_source_citation_verifier_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 26945,
      "sha256": "82a9834bef921ebefd6aedb360dfb4a07e5d8ba2798c66f6a8642c054097b6a6",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-014",
      "file_name": "14_conflict_detector_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 41119,
      "sha256": "a9e9cefe61a54cbff5f2d276c4bd7f184164f8888c17e0dd9d7105250b2dc152",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-015",
      "file_name": "15_ssot_candidate_extractor_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 41910,
      "sha256": "7eba7a49a42ea3982227e1038760fcd7783574af5d0445f6115bf913f0416fd0",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-016",
      "file_name": "16_financial_signal_extractor_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 44174,
      "sha256": "73674eaf7d49765263c3af66c61bd5fdd11eaf4022c23f2e4f45d4918d62c8b5",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-017",
      "file_name": "17_risk_signal_extractor_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 41796,
      "sha256": "203d4eada1beb3fa0faf656a8913e6acaf6201d7a1a5db0dfa3aa49d24abed74",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-018",
      "file_name": "18_document_priority_ranker_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 34857,
      "sha256": "d4ea97c4931c0acd6c277440eeeae42adc393698eac6835f2c50b97ffd182236",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-019",
      "file_name": "19_night_run_orchestrator_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 33677,
      "sha256": "a12c5c5526fcc5bb2bcb9f3ba012fe2f34d4d0079e7c4666f06ce4194db57d30",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-020",
      "file_name": "20_rag_control_tower_export_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 31352,
      "sha256": "69433ae04555a9b4e3d50190a4a13be3739590c71902b88db722ed15877e826c",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-021",
      "file_name": "21_executive_report_pack_builder_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 30459,
      "sha256": "d9179254a06c95f5e30db352ab7560b83466845ee5565e75e665502e38d9bd16",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-022",
      "file_name": "22_lender_due_diligence_pack_builder_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 45066,
      "sha256": "f429d92ab3f014f81c525a209144e524f9cef9b1985a099f93318d8b0215c521",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-023",
      "file_name": "23_board_decision_memo_builder_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 41079,
      "sha256": "713030b0f6eb64409e35eef08e3a49651bcdc3a256a5ae68d424248225730198",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-024",
      "file_name": "24_legal_compliance_gap_analyzer_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 44171,
      "sha256": "bfb273a031c0f0d881b8a0ea3374bf66b47f128d2101e1e1ad382a2ccf21acb6",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-025",
      "file_name": "25_esg_permitting_risk_analyzer_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 45478,
      "sha256": "bb29cc2115a8b2023160a8dfc4ca0fe50ed68c98ae95d58e0b2e66767a040f64",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-026",
      "file_name": "26_capex_loan_bankability_analyzer_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 55083,
      "sha256": "77345f31efcfa83f3df9cf5213e795d84d00b40f60f3ac9937431f81c71c95f9",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-027",
      "file_name": "27_investor_data_room_freeze_builder_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 30784,
      "sha256": "576e1d9cdc91f6c67feb547b4892bea5cfb00bcc1254d8cdb9c520247f9b0f6c",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-028",
      "file_name": "28_distribution_readiness_gatekeeper_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 37511,
      "sha256": "5ae7bdb8348585752c89e8f847a5b98c6213efe9b4332b8cc562c6e3ba0c9da8",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-029",
      "file_name": "29_external_release_package_builder_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 29576,
      "sha256": "4831f89e57107110e5637e058e3893711c6347cbc6400c5a8837efe14bdcf96d",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-030",
      "file_name": "30_post_release_audit_and_receipt_register_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 33532,
      "sha256": "8d247df6430b4c2a7be1c209e5cbe498d5e1cedd882413b3c468105c14a7ef95",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-031",
      "file_name": "31_ssot_alignment_validator_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 38523,
      "sha256": "d295bbf4fc033e0836293967881a9efd5ffaf5f0584ed62b174ea564ba797a90",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-032",
      "file_name": "32_sovereign_charter_v60_1_builder_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 51579,
      "sha256": "d5c98e267f0e8dd30c6a13c7a1843e4b3fb9a62cc124ae8a6c8c99fd1410c4f8",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-033",
      "file_name": "33_kernel_to_full_rag_bridge_mapper_v2_AUDIT_LOCKED.py",
      "file_type": "py",
      "size_bytes": 41949,
      "sha256": "1abddc55523b4b4243d413ea346f4d5fdc2539c664caae7937192a8389bbae26",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-034",
      "file_name": "TITAN_DEEP_FORENSIC_CONTEXT_EXTRACTION_RAG_READY.md",
      "file_type": "md",
      "size_bytes": 34481,
      "sha256": "d51645d79b7dd0a71a4625f54b5b8121af308c84f525ed476f9dc1e8334de2f1",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-035",
      "file_name": "TITAN_KERNEL_SCRIPTS_inventory_snapshot.md",
      "file_type": "md",
      "size_bytes": 2046,
      "sha256": "866a3afdcbaca57bfba34f2604895fc7e6eb1ff6b013c446cf699e9777f8d35a",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-036",
      "file_name": "TITAN_MASTER_SSOT_v1.0.pdf",
      "file_type": "pdf",
      "size_bytes": 15425,
      "sha256": "6defc09cb75223b941f2ee53930bffd6466ffbd8b25e795b28a783347f4fd3d7",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-037",
      "file_name": "TITAN_SINGLE_SOURCE_OF_TRUTH_EXTRACT.md",
      "file_type": "md",
      "size_bytes": 24552,
      "sha256": "a4c7292a2841b435b85e477624fba4dca8e8edfea4e4a35452912a5c52505458",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-038",
      "file_name": "TITAN_ready_to_copy_excel_inventory_extraction.tsv",
      "file_type": "tsv",
      "size_bytes": 43319,
      "sha256": "56a039522c834a262409e92e6710d034ccf6f672777fdfbb548a676219706851",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-039",
      "file_name": "create_titan_grid_v60_5_omega.ps1",
      "file_type": "ps1",
      "size_bytes": 11695,
      "sha256": "d9dbf0a1787cc61728a6f5d19a54629732813032c8ca038af0c707ad71a65873",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-040",
      "file_name": "create_titan_grid_v60_5_omega_FORENSIC_LOCKED_PATCH.ps1",
      "file_type": "ps1",
      "size_bytes": 16633,
      "sha256": "eb8719b666ac9334052a57a0f6b7a5e4d9e49f48042779569f3ce310f74fbf2f",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    },
    {
      "artifact_id": "ART-041",
      "file_name": "create_titan_grid_v60_5_omega_ORIGINAL_EXACT.ps1",
      "file_type": "ps1",
      "size_bytes": 11695,
      "sha256": "d9dbf0a1787cc61728a6f5d19a54629732813032c8ca038af0c707ad71a65873",
      "source_context": "current_session_available_artifact",
      "treatment": "CRYPTOGRAPHIC_REFERENCE_ONLY",
      "final_use_allowed": "NO"
    }
  ]
}
```

## 5. [GLOBALNE KONTROLE I BLOKERI]

```json
{
  "classification": "GLOBAL_CONTROLS",
  "controls": [
    [
      "FINAL_USE_ALLOWED",
      "NO",
      "CRITICAL"
    ],
    [
      "SSOT_WRITE_ALLOWED",
      "NO",
      "CRITICAL"
    ],
    [
      "EVIDENCE_APPROVAL_ALLOWED",
      "NO",
      "CRITICAL"
    ],
    [
      "GATE_CLOSURE_ALLOWED",
      "NO",
      "CRITICAL"
    ],
    [
      "SYSTEM_STATUS",
      "RED",
      "CRITICAL"
    ],
    [
      "STEP102_STATUS",
      "LOCKED / NOT ACCEPTED",
      "CRITICAL"
    ],
    [
      "P0_GATES",
      "10/10 BLOCKED",
      "CRITICAL"
    ],
    [
      "RISK_BASELINE",
      890,
      "CRITICAL"
    ],
    [
      "NO_DIRECT_MERGE",
      "Kernel and Full RAG cannot merge directly",
      "CRITICAL"
    ],
    [
      "NO_SIGNAL_WITHOUT_SOURCE_PATH",
      "source_path mandatory",
      "HIGH"
    ],
    [
      "NO_SOURCE_WITHOUT_HASH",
      "sha256 mandatory",
      "HIGH"
    ]
  ]
}
```

## 6. [RAG MIGRATION RECORDS]

```json
{
  "recommended_collections": [
    [
      "financial_matrix",
      "FINANSIJSKA_MATRICA",
      "P0",
      "REVIEW_REQUIRED_FINANCIAL_ASSUMPTION"
    ],
    [
      "operational_parameters",
      "OPERATIVNI_PARAMETRI",
      "P0",
      "REVIEW_REQUIRED_TECHNICAL_PARAMETER"
    ],
    [
      "institutional_creditors",
      "INSTITUCIONALNI_KREDITORI",
      "P0",
      "REVIEW_REQUIRED_EVIDENCE_SIGNAL"
    ],
    [
      "cryptographic_chain",
      "KRIPTOGRAFSKI_LANAC",
      "P0",
      "CONTROL_DIAMOND"
    ],
    [
      "global_controls",
      "GLOBAL_CONTROLS",
      "P0",
      "CONTROL_DIAMOND"
    ]
  ],
  "required_next_evidence_before_step103": [
    "STEP102 blocker closure register",
    "P0 gate closure evidence",
    "evidence gap closure evidence",
    "CAPEX source file and approval lineage",
    "OPEX base case",
    "DSCR/IRR/NPV/WACC model",
    "collateral valuation and legal title evidence",
    "grant/MIA documentation",
    "EIB/EBRD eligibility and PR1-10 evidence matrix",
    "transformer technical specification pack",
    "OEE calculation model",
    "location/site/permitting evidence",
    "Control Tower lock policy",
    "Kernel to Full RAG adapter schema"
  ],
  "migration_decision": "INGEST_AS_REVIEW_REQUIRED_RECORDS_ONLY",
  "final_use_allowed": "NO"
}
```

## FINAL LOCK

```text
SYSTEM RED — STEP102 LOCKED — NO FINAL USE
```
