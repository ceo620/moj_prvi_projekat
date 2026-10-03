# TITAN / TUZI NEXUS — FORENZIČKA EKSTRAKCIJA KONTEKSTA ZA RAG PIPELINE

**Document type:** RAG-ready forensic extraction  
**Scope:** dostupni kontekst ove konverzacije + trajno zabilježene TITAN memorije iz prethodnih povezanih razmjena  
**Extraction mode:** engineering / finance / audit facts only  
**Excluded:** marketinška hiperbola, nevalidirane garancije, prazne rasprave  
**Canonical status:** `REPORT_ONLY / EVIDENCE_GATE_OPEN`  
**Final GO status:** nije odobren  

---

## 0. KANONSKI STATUS I OGRANIČENJA EKSTRAKCIJE

```json
{
  "extraction_status": "REPORT_ONLY",
  "evidence_gate": "OPEN",
  "final_authorization": "NOT_GRANTED",
  "go_status_allowed": false,
  "reason": "Financial, legal, technical, ESG and forensic gates are not formally closed.",
  "source_scope": [
    "visible conversation content",
    "retained TITAN project memory",
    "previously extracted script and document facts"
  ],
  "non_evidence_claims_removed": [
    "Validated CAPEX without evidence pack",
    "Fully compliant JPP without legal opinion",
    "100% elimination of 19.9M discrepancy",
    "Zero latency technical interface",
    "Guaranteed information integrity",
    "GO - AUTHORIZED before evidence gates"
  ]
}
```

---

# 1. [FINANSIJSKA MATRICA]

## 1.1. Kanonski finansijski anchor-i

```json
{
  "financial_anchors": {
    "current_project_phase": {
      "phase_id": "Phase 102",
      "status": "WORKING",
      "capex_eur": 43500000,
      "capex_label": "Sovereign 43.5M working investment case",
      "evidence_status": "EVIDENCE_PENDING",
      "approval_status": "NOT_AUDIT_LOCKED",
      "notes": "CAPEX 43.5M je aktivni radni anchor, ali ne smije biti opisan kao validated bez formalnog evidence pack-a."
    },
    "legacy_anchor": {
      "capex_eur": 19900000,
      "status": "LEGACY_CONFLICT_ANCHOR",
      "treatment": "Do not delete. Reconcile through CAPEX Delta Reconciliation Note.",
      "evidence_status": "CONFLICT_REQUIRES_RECONCILIATION"
    },
    "transition": {
      "from": "Phase 102",
      "to": "STEP103",
      "status": "REFERENCED_NOT_FULLY_DEFINED",
      "required_action": "Define STEP103 financial scope, approvals, delta bridge, evidence gates and updated SSOT record."
    }
  }
}
```

## 1.2. CAPEX matrica

```json
{
  "capex_matrix": [
    {
      "item": "Total CAPEX",
      "amount_eur": 43500000,
      "currency": "EUR",
      "status": "WORKING_LENDER_REVIEW_CASE",
      "allowed_wording": "Current working investment case, subject to SSOT approval, lender review and supporting evidence validation.",
      "prohibited_wording": "Validated / final / approved without evidence pack"
    },
    {
      "item": "Legacy CAPEX",
      "amount_eur": 19900000,
      "currency": "EUR",
      "status": "LEGACY_REFERENCE",
      "allowed_wording": "Legacy anchor requiring reconciliation against EUR 43.5M.",
      "prohibited_wording": "100% eliminated discrepancy"
    },
    {
      "item": "CAPEX Delta",
      "amount_eur": 23600000,
      "currency": "EUR",
      "calculation": "43.5M - 19.9M",
      "status": "RECONCILIATION_REQUIRED",
      "required_document": "CAPEX_Delta_Reconciliation_Note"
    }
  ]
}
```

## 1.3. Finansijski pokazatelji

```json
{
  "financial_kpis": {
    "dscr": {
      "value": 1.38,
      "unit": "x",
      "status": "PLANNING_ASSUMPTION",
      "allowed_wording": "DSCR of 1.38x is presented as a planning assumption and remains subject to lender model validation and covenant review.",
      "prohibited_wording": "Sovereign Stable / Validated / final covenant"
    },
    "irr": {
      "value": null,
      "status": "TO_BE_MODELLED",
      "required_inputs": [
        "Revenue model",
        "OPEX model",
        "Debt schedule",
        "Tax assumptions",
        "Depreciation schedule",
        "Terminal value or project life assumption",
        "Sensitivity analysis"
      ],
      "prohibited_wording": "Targeted Tier-1 Infrastructure Grade without numeric IRR and scenario model"
    },
    "npv": {
      "value": null,
      "status": "TO_BE_MODELLED"
    },
    "wacc": {
      "value": null,
      "status": "TO_BE_MODELLED",
      "notes": "WACC must account for sovereign / Montenegro risk, funding mix, debt terms and lender assumptions."
    }
  }
}
```

## 1.4. OPEX pretpostavke

```json
{
  "opex_matrix": {
    "status": "NOT_SPECIFIED_IN_AVAILABLE_CONTEXT",
    "known_values": [],
    "required_for_step103": [
      "Labor costs",
      "Energy costs",
      "Maintenance",
      "Insurance",
      "Lease or land cost if applicable",
      "Utilities",
      "Raw material and components",
      "Logistics",
      "Compliance and permitting",
      "Administrative overhead",
      "Debt service related fees",
      "Contingency"
    ],
    "rag_tag": "OPEX_MISSING_REQUIRE_MODEL"
  }
}
```

## 1.5. Budžetske alokacije i prethodno pomenute reference

```json
{
  "budget_allocation_references": [
    {
      "source_context": "Earlier CAPEX model snippets in retained memory",
      "line_item": "LOG-001 Logistics",
      "amount_eur": 14088000,
      "percentage_of_total": 19.9,
      "base_total_eur": 70200000,
      "status": "HISTORICAL_SNIPPET_NOT_CURRENT_CANON",
      "action": "Do not merge into Phase 102 43.5M model without reconciliation."
    },
    {
      "source_context": "Earlier CAPEX model snippets in retained memory",
      "line_item": "CIVIL-001 Civil Works",
      "amount_eur": 17900000,
      "percentage_of_total": 28.5,
      "base_total_eur": null,
      "status": "HISTORICAL_SNIPPET_NOT_CURRENT_CANON",
      "action": "Requires source validation before inclusion."
    }
  ]
}
```

## 1.6. Finansijske evidence gates

```json
{
  "financial_evidence_gates": [
    {
      "gate": "CAPEX_BREAKDOWN",
      "required": true,
      "status": "OPEN",
      "required_artifacts": [
        "Full EUR 43.5M CAPEX breakdown",
        "Vendor / EPC quotes if available",
        "Budget allocation by workstream",
        "Contingency basis",
        "VAT / tax treatment",
        "FX assumptions if applicable"
      ]
    },
    {
      "gate": "CAPEX_DELTA_RECONCILIATION",
      "required": true,
      "status": "OPEN",
      "required_artifacts": [
        "19.9M vs 43.5M bridge",
        "Scope change memo",
        "Approval note",
        "Model version comparison"
      ]
    },
    {
      "gate": "DSCR_VALIDATION",
      "required": true,
      "status": "OPEN",
      "required_artifacts": [
        "Debt schedule",
        "Revenue assumptions",
        "OPEX assumptions",
        "Lender covenant sheet",
        "Base/downside/upside scenario"
      ]
    },
    {
      "gate": "IRR_NPV_WACC",
      "required": true,
      "status": "OPEN",
      "required_artifacts": [
        "Financial model",
        "Sensitivity analysis",
        "Discount rate memo",
        "Investment committee assumptions"
      ]
    }
  ]
}
```

---

# 2. [OPERATIVNI PARAMETRI]

## 2.1. Lokacije i entiteti

```json
{
  "locations_and_entities": {
    "primary_location": {
      "name": "Tuzi",
      "country": "Montenegro",
      "role": "Project / industrial / infrastructure location",
      "status": "CANONICAL_PROJECT_LOCATION"
    },
    "related_location": {
      "name": "Podgorica",
      "country": "Montenegro",
      "role": "Regional / administrative / operational reference",
      "status": "REFERENCED"
    },
    "corporate_reference": {
      "name": "Ars Metal Industries",
      "role": "Industrial / project entity reference",
      "status": "REFERENCED_REQUIRES_CORPORATE_EVIDENCE"
    },
    "grid_stakeholders": [
      {
        "name": "CGES",
        "role": "Transmission/grid stakeholder reference",
        "status": "REFERENCE_ONLY_PENDING_GRID_EVIDENCE"
      },
      {
        "name": "CEDIS",
        "role": "Distribution/grid stakeholder reference",
        "status": "REFERENCE_ONLY_PENDING_GRID_EVIDENCE"
      },
      {
        "name": "EPCG",
        "role": "Utility / energy-sector contextual stakeholder",
        "status": "REFERENCE_ONLY"
      }
    ]
  }
}
```

## 2.2. OEE cilj

```json
{
  "operational_kpis": {
    "oee_target": {
      "value": 85,
      "unit": "%",
      "status": "TARGET",
      "context": "Operational efficiency target referenced by user",
      "required_validation": [
        "Production line design",
        "Shift model",
        "Planned downtime",
        "Maintenance schedule",
        "Quality loss assumptions",
        "Ramp-up curve"
      ]
    }
  }
}
```

## 2.3. Ekološki transformatori / tehnički proizvodni okvir

```json
{
  "eco_transformer_specifications": {
    "product_family": [
      "Transformers",
      "Power transformers",
      "Distribution transformers",
      "Oil-immersed transformers",
      "Eco transformer concept"
    ],
    "status": "CONCEPT_REFERENCED_NOT_TECHNICALLY_LOCKED",
    "known_voltage_references": [
      "110 kV",
      "220 kV",
      "400 kV"
    ],
    "technical_specs_missing": [
      "Rated power MVA/kVA",
      "Voltage class per product",
      "Cooling type",
      "Insulation class",
      "Oil type / ester fluid if eco design",
      "Loss levels",
      "IEC / EN standards",
      "Testing protocol",
      "Grid-code requirements",
      "Environmental performance metrics"
    ],
    "required_documents": [
      "Technical product datasheets",
      "Manufacturing process specification",
      "Quality assurance plan",
      "Factory acceptance test protocol",
      "Environmental product note",
      "Independent technical review"
    ]
  }
}
```

## 2.4. Mrežna integracija

```json
{
  "grid_integration": {
    "claimed_in_original_v888": "CGES & CEDIS High-Voltage Synchronization Active",
    "forensic_status": "UNVERIFIED_CLAIM",
    "audit_safe_rewrite": "Grid interface assumptions involving CGES and CEDIS remain subject to technical review, grid connection evidence and independent validation.",
    "evidence_required": [
      "Grid connection study",
      "Connection approval or application status",
      "Technical conditions from grid operator",
      "Single-line diagram",
      "Load profile",
      "Protection and metering concept",
      "Interface responsibility matrix"
    ]
  }
}
```

## 2.5. Zabranjene tehničke tvrdnje

```json
{
  "prohibited_technical_claims": [
    {
      "claim": "Zero Latency Data/Energy Interface",
      "reason": "Technically indefensible and not evidence-based.",
      "replacement": "Subject to independent technical validation, interface testing and operational readiness assessment."
    },
    {
      "claim": "High-Voltage Synchronization Active",
      "reason": "Requires documentary proof from grid stakeholders.",
      "replacement": "Grid interface assumptions remain under technical review."
    }
  ]
}
```

---

# 3. [INSTITUCIONALNI KREDITORI]

## 3.1. Institucionalni okvir

```json
{
  "institutional_creditor_framework": {
    "target_creditors": [
      "EIB",
      "EBRD"
    ],
    "document_standard": "Bankable lender-review documentation",
    "tone": "Conservative, evidence-based, non-promotional",
    "status": "TARGET_ALIGNMENT_NOT_FORMAL_APPROVAL",
    "core_requirements": [
      "Transparent CAPEX and OPEX model",
      "Debt service and DSCR validation",
      "Legal basis and procurement compliance",
      "Environmental and social due diligence",
      "Corporate authority evidence",
      "Technical feasibility",
      "Forensic document traceability",
      "VDR completeness",
      "Risk matrix and mitigation plan"
    ]
  }
}
```

## 3.2. EIB-aligned requirements

```json
{
  "eib_alignment": {
    "status": "TARGET_STANDARD",
    "not_confirmed_as": "EIB approval or formal compliance",
    "required_artifacts": [
      "Investment rationale",
      "Economic justification",
      "Financial model",
      "Procurement plan",
      "Environmental and social documentation",
      "Risk allocation matrix",
      "Implementation schedule",
      "Governance and reporting framework",
      "Audit trail and document register"
    ],
    "language_rule": "Use 'subject to review' unless formal EIB evidence exists."
  }
}
```

## 3.3. EBRD PR1-10 alignment matrix

```json
{
  "ebrd_pr_1_10_alignment": [
    {
      "pr": "PR1",
      "topic": "Assessment and Management of Environmental and Social Impacts and Issues",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["ESG screening", "Environmental and Social Management Plan", "Risk register", "Impact assessment"]
    },
    {
      "pr": "PR2",
      "topic": "Labour and Working Conditions",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["HR policy", "Worker safety plan", "Employment standards", "Grievance mechanism"]
    },
    {
      "pr": "PR3",
      "topic": "Resource Efficiency and Pollution Prevention and Control",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["Energy/resource efficiency note", "Pollution prevention plan", "Waste management approach", "Transformer oil/environmental controls"]
    },
    {
      "pr": "PR4",
      "topic": "Health, Safety and Security",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["HSE plan", "Emergency response plan", "Site security concept", "Operational safety assessment"]
    },
    {
      "pr": "PR5",
      "topic": "Land Acquisition, Restrictions on Land Use and Involuntary Resettlement",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["Land title evidence", "Site control documentation", "Resettlement screening if applicable"]
    },
    {
      "pr": "PR6",
      "topic": "Biodiversity Conservation and Sustainable Management of Living Natural Resources",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["Biodiversity screening", "Site environmental baseline", "Mitigation measures if applicable"]
    },
    {
      "pr": "PR7",
      "topic": "Indigenous Peoples",
      "project_status": "LIKELY_NOT_APPLICABLE_BUT_REQUIRES_SCREENING",
      "required_project_artifacts": ["Applicability screening"]
    },
    {
      "pr": "PR8",
      "topic": "Cultural Heritage",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["Cultural heritage screening", "Chance-find procedure if construction applies"]
    },
    {
      "pr": "PR9",
      "topic": "Financial Intermediaries",
      "project_status": "CONDITIONAL",
      "required_project_artifacts": ["Applicability check depending on financing structure"]
    },
    {
      "pr": "PR10",
      "topic": "Information Disclosure and Stakeholder Engagement",
      "project_status": "EVIDENCE_PENDING",
      "required_project_artifacts": ["Stakeholder Engagement Plan", "Disclosure plan", "Grievance mechanism", "Consultation log"]
    }
  ]
}
```

## 3.4. Legal / PPP / JPP status

```json
{
  "legal_and_ppp_status": {
    "original_claim": "Fully compliant with Law on JPP",
    "forensic_status": "UNVERIFIED",
    "allowed_wording": "The proposed structure remains subject to legal review under the applicable PPP/JPP framework and public procurement requirements.",
    "required_artifacts": [
      "Legal opinion",
      "PPP/JPP applicability memo",
      "Procurement route analysis",
      "Government approvals if applicable",
      "Concession or public-private structure documents if applicable"
    ]
  }
}
```

## 3.5. Corporate authority evidence

```json
{
  "corporate_authority": {
    "items_referenced": [
      "CRPS",
      "Statute",
      "Director mandates"
    ],
    "forensic_status": "REFERENCED_REQUIRES_VDR_EVIDENCE",
    "allowed_wording": "Corporate authority documents are subject to VDR evidence verification.",
    "required_artifacts": [
      "CRPS extract",
      "Company statute",
      "Director appointment / mandate",
      "Board or shareholder approval where required",
      "Authorized signatory evidence"
    ]
  }
}
```

---

# 4. [KRIPTOGRAFSKI LANAC]

## 4.1. Sačuvani SHA-256 heševi

```json
{
  "sha256_hashes": [
    {
      "artifact": "TITAN_DEEP_HARVEST_V4.ps1",
      "sha256": "2108e104e46e7d4f06b3f54c1efae2062b0e8f654e0b572004cb6fc643ee075d",
      "path": "C:\\Users\\Korisnik\\Desktop\\02_BACKUP_ARCHIVES",
      "status": "FORENSICALLY_INSPECTED_NOT_AUDIT_APPROVED",
      "notes": "Script scans for CAPEX, DSCR, TUZI, CGES, CEDIS, LOAN, COVENANT and compares 43.5M vs legacy 19.9M."
    },
    {
      "artifact": "TITAN_V888_SSOT_Finalne_Tacke.md",
      "sha256": "536bbffb00f6619820206871d6885b912ac16a94222eb82aa65aac36bf070767",
      "path": "/mnt/data/TITAN_V888_SSOT_Finalne_Tacke.md",
      "status": "GENERATED_FROM_VISIBLE_CONVERSATION",
      "notes": "Previous SSoT extraction generated during this conversation."
    }
  ]
}
```

## 4.2. Hash pravila

```json
{
  "hashing_rules": {
    "rule_1": "Do not write SHA-256 into the same file that is being hashed.",
    "reason_1": "The file content changes, invalidating the hash.",
    "correct_structure": [
      "primary_document.txt",
      "primary_document.manifest.json",
      "primary_document.hash.txt"
    ],
    "minimum_manifest_fields": [
      "document_path",
      "document_name",
      "sha256",
      "created_at",
      "system_status",
      "evidence_status",
      "authorizing_protocol"
    ]
  }
}
```

## 4.3. Manifest template

```json
{
  "manifest_template": {
    "document_path": "ABSOLUTE_PATH_TO_ARTIFACT",
    "document_name": "ARTIFACT_NAME",
    "sha256": "SHA256_HEX_DIGEST",
    "created_at": "ISO_8601_TIMESTAMP",
    "system_status": "REPORT_ONLY",
    "evidence_status": "EVIDENCE_GATE_OPEN",
    "authorizing_protocol": "TITAN_CANONICAL_HEADER_V1",
    "destructive_operations": false,
    "controlled_write": true,
    "source_files_modified": false
  }
}
```

## 4.4. Merkle / immutable index

```json
{
  "merkle_index_rules": {
    "status": "ACCEPTED_FOR_GROUP_LOCKING",
    "allowed_use": [
      "Batch document integrity proof",
      "VDR package hash chain",
      "Multi-file immutable index"
    ],
    "minimum_fields": [
      "artifact_path",
      "artifact_sha256",
      "artifact_size_bytes",
      "created_or_modified_timestamp",
      "evidence_status",
      "document_class",
      "merkle_leaf_hash",
      "merkle_root"
    ],
    "prohibited_use": [
      "Marketing-only immutable claims",
      "Hash reference without manifest",
      "GO authorization without evidence gate closure"
    ]
  }
}
```

---

# 5. KANONSKE SKRIPTE I SISTEMSKI MODULI

```json
{
  "canonical_scripts": {
    "bootstrap_and_config": [
      "00_SETUP_STRUCTURE.py v2.1/v3.0/v3.1 HARDENED",
      "00_CREATE_TITAN_DESKTOP_STRUCTURE.ps1 v5.0 FULL POWER",
      "01_config_init.py"
    ],
    "database_and_ingestion": [
      "02_DATABASE_INIT.py v2.1/v3 target",
      "01_TITAN_ELITE_RECONSTRUCTOR.py",
      "03_v31_producer.py",
      "03_v29_queue_consumer.py"
    ],
    "runtime_monitoring_sync": [
      "06_kernel_live_mode_v1_1.py",
      "06_kernel_live_mode_daemon.py",
      "07_status_monitor_v1.py",
      "08_sync_sqlite_to_existing_control_tower.py"
    ],
    "ssot_register_packaging": [
      "04_ssot_generator.py",
      "09_document_register_builder.py",
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
      "TITAN_FINAL_HARMONIZED_CONTROL_v9.ps1"
    ],
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
    ]
  }
}
```

---

# 6. PUTANJE I FOLDERI

```json
{
  "canonical_paths": [
    {
      "label": "V888 Executive Summary",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FINAL_VDR_SOVEREIGN\\02_FINANCIAL_ARCHITECTURE_SOVEREIGN_43.5M\\TITAN_EXEC_SUMMARY_V888.txt",
      "status": "REFERENCED"
    },
    {
      "label": "Backup archives / Deep Harvest target",
      "path": "C:\\Users\\Korisnik\\Desktop\\02_BACKUP_ARCHIVES",
      "status": "REFERENCED"
    },
    {
      "label": "Working export folder",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_WORKING_FILES_EXPORT_888",
      "status": "REFERENCED"
    },
    {
      "label": "TITAN kernel scripts",
      "path": "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS",
      "status": "REFERENCE_FROM_PRIOR_CONTEXT"
    },
    {
      "label": "V31 queue",
      "path": "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS\\00_QUEUE\\queue.jsonl",
      "status": "REFERENCE_FROM_PRIOR_CONTEXT"
    },
    {
      "label": "V29 SQLite state DB",
      "path": "C:\\Users\\Lenovo\\Desktop\\TITAN_KERNEL_SCRIPTS\\03_ORCHESTRATION\\v29_state.db",
      "status": "REFERENCE_FROM_PRIOR_CONTEXT"
    },
    {
      "label": "Control Tower workbook",
      "path": "C:\\Users\\Lenovo\\Desktop\\TITAN_GRID\\00_SYSTEM\\00_CONTROL_TOWER\\Control_Tower.xlsx",
      "status": "REFERENCE_FROM_PRIOR_CONTEXT"
    },
    {
      "label": "Document Register",
      "path": "C:\\Users\\Lenovo\\Desktop\\TITAN_GRID\\01_VDR_GOVERNANCE\\01_MASTER_INDEX\\Document_Register.xlsx",
      "status": "REFERENCE_FROM_PRIOR_CONTEXT"
    },
    {
      "label": "Local Evidence RAG spec",
      "path": "C:\\Users\\Korisnik\\Desktop\\TITAN_FULL_RAG\\TITAN_LOCAL_EVIDENCE_RAG_ENGINE_v1.0_SPEC.md",
      "status": "REFERENCE_FROM_PRIOR_CONTEXT"
    }
  ]
}
```

---

# 7. AUDIT-SAFE POWERSHELL STANDARD

```json
{
  "powershell_minimum_standard": {
    "required_lines": [
      "Set-StrictMode -Version Latest",
      "$ErrorActionPreference = \"Stop\""
    ],
    "required_behaviors": [
      "Create output directory if missing",
      "Use UTF-8 output",
      "Write companion manifest",
      "Compute SHA-256 after writing artifact",
      "Do not embed final hash inside the hashed artifact",
      "Do not silently catch errors",
      "Log execution status"
    ],
    "safe_directory_creation": "if (!(Test-Path $Folder)) { New-Item -ItemType Directory -Path $Folder -Force | Out-Null }",
    "safe_output": "$Content | Out-File -FilePath $Path -Encoding utf8"
  }
}
```

## 7.1. SYSTEM RED / REPORT_ONLY zabrane

```json
{
  "report_only_restrictions": {
    "prohibited_operations": [
      "Delete files",
      "Quarantine files without explicit approval",
      "Rename files",
      "Move files",
      "Overwrite source evidence",
      "Auto-fix source evidence",
      "Declare GO - AUTHORIZED"
    ],
    "allowed_operations": [
      "Read",
      "Scan",
      "Hash",
      "Create report",
      "Create snapshot",
      "Create manifest",
      "Create controlled new output artifact"
    ]
  }
}
```

---

# 8. VDR / SSOT / DOCUMENT CONTROL

## 8.1. VDR minimum set

```json
{
  "vdr_minimum_artifacts": [
    "Executive Summary",
    "CAPEX model",
    "OPEX model",
    "DSCR / lender model",
    "CAPEX Delta Reconciliation Note",
    "Legal evidence pack",
    "Corporate authority evidence",
    "Technical/grid evidence",
    "ESG/permitting evidence",
    "Forensic manifest",
    "Hash register",
    "Document register",
    "Risk matrix",
    "Stakeholder engagement evidence if EBRD PR10 applies"
  ]
}
```

## 8.2. SSOT status taxonomy

```json
{
  "ssot_status_taxonomy": [
    "DRAFT",
    "WORKING",
    "EVIDENCE_PENDING",
    "APPROVED",
    "AUDIT_LOCKED",
    "REJECTED",
    "LEGACY_CONFLICT_ANCHOR",
    "RECONCILIATION_REQUIRED"
  ]
}
```

## 8.3. Evidence gate model

```json
{
  "evidence_gates": [
    {
      "gate": "FINANCIAL_GATE",
      "status": "OPEN",
      "close_condition": "CAPEX/OPEX/DSCR/IRR/NPV/WACC model approved and evidence-linked."
    },
    {
      "gate": "LEGAL_GATE",
      "status": "OPEN",
      "close_condition": "Legal opinion, corporate authority and procurement/PPP evidence verified."
    },
    {
      "gate": "TECHNICAL_GATE",
      "status": "OPEN",
      "close_condition": "Technical feasibility, grid interface, product specs and operational readiness validated."
    },
    {
      "gate": "ESG_PERMITTING_GATE",
      "status": "OPEN",
      "close_condition": "ESG screening, permitting status and EBRD PR applicability documented."
    },
    {
      "gate": "FORENSIC_AUDIT_GATE",
      "status": "OPEN",
      "close_condition": "Document register, hash register, manifests, logs and non-destructive audit trail complete."
    }
  ]
}
```

---

# 9. V888 EXECUTIVE SUMMARY FORENSIC FINDINGS

```json
{
  "v888_original_assessment": {
    "status": "NOT_READY_FOR_BANK_OR_MINISTRY_SUBMISSION",
    "primary_risks": [
      "Overstated validation claims",
      "Legal compliance asserted without legal opinion",
      "Technical claims not evidence-backed",
      "GO status declared before evidence gates",
      "SHA-256 seal described without correct manifest structure",
      "Marketing tone exceeds lender-review standard"
    ],
    "required_rewrite_status": {
      "document_status": "DRAFT / LENDER_REVIEW_VERSION",
      "system_status": "REPORT_ONLY",
      "evidence_status": "EVIDENCE_GATE_OPEN",
      "authorization": "NOT_FINAL"
    }
  }
}
```

## 9.1. Forbidden-to-safe wording map

```json
{
  "wording_map": [
    {
      "forbidden": "TOTAL CAPEX: EUR 43.5M Validated",
      "safe": "Total CAPEX of EUR 43.5M is the current working investment case, subject to SSOT approval, lender review and supporting evidence validation."
    },
    {
      "forbidden": "DSCR: 1.38x Sovereign Stable",
      "safe": "DSCR of 1.38x is presented as a planning assumption and remains subject to lender model validation and covenant review."
    },
    {
      "forbidden": "Fully compliant with Law on JPP",
      "safe": "The proposed structure remains subject to legal review under the applicable PPP/JPP framework and public procurement requirements."
    },
    {
      "forbidden": "100% elimination of legacy 19.9M discrepancies",
      "safe": "Legacy 19.9M CAPEX references require reconciliation against the current EUR 43.5M working case."
    },
    {
      "forbidden": "Zero Latency Data/Energy Interface",
      "safe": "The technical architecture remains subject to independent validation, interface testing and operational readiness assessment."
    },
    {
      "forbidden": "GO - AUTHORIZED",
      "safe": "REPORT_ONLY / EVIDENCE_GATE_OPEN"
    }
  ]
}
```

---

# 10. RAG INGESTION TAGS

```json
{
  "rag_tags": {
    "finance": [
      "CAPEX_43_5M",
      "CAPEX_19_9M_LEGACY",
      "CAPEX_DELTA_23_6M",
      "DSCR_1_38_PLANNING",
      "IRR_MISSING",
      "NPV_MISSING",
      "WACC_MISSING",
      "OPEX_MISSING"
    ],
    "operations": [
      "TUZI",
      "PODGORICA",
      "ARS_METAL_INDUSTRIES",
      "OEE_85_TARGET",
      "ECO_TRANSFORMERS",
      "POWER_TRANSFORMERS",
      "DISTRIBUTION_TRANSFORMERS",
      "CGES",
      "CEDIS",
      "EPCG"
    ],
    "creditors": [
      "EIB_TARGET_ALIGNMENT",
      "EBRD_PR1_10_ALIGNMENT",
      "PPP_JPP_REVIEW",
      "LENDER_REVIEW",
      "VDR_REQUIRED"
    ],
    "forensics": [
      "SHA256",
      "MANIFEST_JSON",
      "MERKLE_ROOT",
      "DOCUMENT_REGISTER",
      "HASH_REGISTER",
      "AUDIT_LOCKED",
      "REPORT_ONLY",
      "EVIDENCE_GATE_OPEN"
    ],
    "scripts": [
      "TITAN_DEEP_HARVEST_V4",
      "TITAN_FORENSIC_ENGINE",
      "V31_PRODUCER",
      "V29_CONSUMER",
      "CONTROL_TOWER_SYNC",
      "LOCAL_EVIDENCE_RAG"
    ]
  }
}
```

---

# 11. FINALNA MIGRACIONA MATRICA

```json
{
  "migration_matrix": [
    {
      "domain": "FINANCE",
      "canonical_fact": "Phase 102 uses EUR 43.5M as current working CAPEX anchor.",
      "status": "WORKING",
      "evidence_required": true,
      "destination": "financial_ssot.capex"
    },
    {
      "domain": "FINANCE",
      "canonical_fact": "EUR 19.9M remains legacy CAPEX anchor requiring reconciliation.",
      "status": "RECONCILIATION_REQUIRED",
      "evidence_required": true,
      "destination": "financial_ssot.legacy_capex"
    },
    {
      "domain": "FINANCE",
      "canonical_fact": "DSCR 1.38x is planning assumption, not validated covenant.",
      "status": "EVIDENCE_PENDING",
      "evidence_required": true,
      "destination": "financial_model.dscr"
    },
    {
      "domain": "OPERATIONS",
      "canonical_fact": "OEE target is 85%.",
      "status": "TARGET",
      "evidence_required": true,
      "destination": "operations.kpi.oee"
    },
    {
      "domain": "OPERATIONS",
      "canonical_fact": "Tuzi, Montenegro is the project location.",
      "status": "CANONICAL_REFERENCE",
      "evidence_required": true,
      "destination": "project.location"
    },
    {
      "domain": "CREDITORS",
      "canonical_fact": "EIB and EBRD are target institutional creditor standards, not approvals.",
      "status": "TARGET_ALIGNMENT",
      "evidence_required": true,
      "destination": "lender_framework"
    },
    {
      "domain": "CRYPTO",
      "canonical_fact": "SHA-256 hash must be stored in companion manifest, not inside same hashed file.",
      "status": "RULE_APPROVED",
      "evidence_required": false,
      "destination": "forensic_controls.hashing"
    },
    {
      "domain": "SYSTEM",
      "canonical_fact": "System remains REPORT_ONLY / EVIDENCE_GATE_OPEN until all evidence gates close.",
      "status": "CANONICAL_RULE",
      "evidence_required": false,
      "destination": "governance.status"
    }
  ]
}
```

---

# 12. MACHINE-READABLE SUMMARY

```json
{
  "project": {
    "name": "TITAN / TUZI NEXUS",
    "location": "Tuzi, Montenegro",
    "related_location": "Podgorica, Montenegro",
    "entity_reference": "Ars Metal Industries",
    "phase": "Phase 102",
    "next_transition": "STEP103",
    "system_status": "REPORT_ONLY",
    "evidence_gate": "OPEN"
  },
  "finance": {
    "capex_current_eur": 43500000,
    "capex_legacy_eur": 19900000,
    "capex_delta_eur": 23600000,
    "dscr": 1.38,
    "dscr_status": "PLANNING_ASSUMPTION",
    "irr": null,
    "npv": null,
    "wacc": null,
    "opex": null
  },
  "operations": {
    "oee_target_percent": 85,
    "products": [
      "eco transformers",
      "power transformers",
      "distribution transformers",
      "oil-immersed transformers"
    ],
    "grid_stakeholders": [
      "CGES",
      "CEDIS",
      "EPCG"
    ]
  },
  "institutional_creditors": {
    "target_frameworks": [
      "EIB",
      "EBRD PR1-10",
      "PPP/JPP review",
      "public procurement review"
    ],
    "approval_status": "NOT_APPROVED",
    "compliance_status": "SUBJECT_TO_REVIEW"
  },
  "crypto_chain": {
    "known_sha256": {
      "TITAN_DEEP_HARVEST_V4.ps1": "2108e104e46e7d4f06b3f54c1efae2062b0e8f654e0b572004cb6fc643ee075d",
      "TITAN_V888_SSOT_Finalne_Tacke.md": "536bbffb00f6619820206871d6885b912ac16a94222eb82aa65aac36bf070767"
    },
    "hash_policy": "Store hash in separate manifest/hash file, never inside same hashed artifact.",
    "manifest_required": true,
    "merkle_supported": true
  }
}
```
