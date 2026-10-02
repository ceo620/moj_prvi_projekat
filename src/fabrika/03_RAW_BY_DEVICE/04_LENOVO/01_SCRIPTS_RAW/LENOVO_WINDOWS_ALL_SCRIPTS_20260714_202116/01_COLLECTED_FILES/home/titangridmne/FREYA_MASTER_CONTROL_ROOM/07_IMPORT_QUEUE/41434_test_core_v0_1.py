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
# WRITE_APPROVED_FOR_TEST_FIXTURES_AND_UNIT_TESTS_ONLY
# NO_UNKNOWN_SCRIPT_EXECUTION_AUTHORIZED

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from delta_ecs.contracts.safe_io import Operation, SafeIOError, default_policy
from delta_ecs.core.hashing import hash_evidence_file
from delta_ecs.core.duplicate_detection import EvidenceIdentity, detect_duplicate_groups
from delta_ecs.core.forbidden_language import scan_text_for_forbidden_language
from delta_ecs.core.evidence_gaps import EvidenceRule, ObservedEvidence, detect_evidence_gaps


class DeltaCoreTests(unittest.TestCase):
    def setUp(self):
        self.project_root = PROJECT_ROOT
        self.fixture_root = PROJECT_ROOT / "tests" / "fixtures_safe"
        self.policy = default_policy(
            project_root=self.project_root,
            approved_source_roots=(self.fixture_root,),
        )

    def test_safe_io_blocks_delete(self):
        with self.assertRaises(SafeIOError):
            self.policy.assert_operation_allowed(
                Operation.DELETE,
                self.fixture_root / "alpha.txt",
            )

    def test_hashing_returns_sha256(self):
        result = hash_evidence_file(
            file_path=self.fixture_root / "alpha.txt",
            source_root=self.fixture_root,
            source_root_id="fixtures_safe",
            policy=self.policy,
        )
        self.assertEqual(len(result.sha256), 64)
        self.assertEqual(result.filename, "alpha.txt")

    def test_duplicate_detection(self):
        a = hash_evidence_file(self.fixture_root / "alpha.txt", self.fixture_root, "fixtures_safe", self.policy)
        b = hash_evidence_file(self.fixture_root / "alpha_copy.txt", self.fixture_root, "fixtures_safe", self.policy)

        groups = detect_duplicate_groups([
            EvidenceIdentity(a.evidence_id, a.sha256, a.size_bytes, a.source_root_id, a.relative_path),
            EvidenceIdentity(b.evidence_id, b.sha256, b.size_bytes, b.source_root_id, b.relative_path),
        ])

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].file_count, 2)

    def test_forbidden_language_detection(self):
        findings = scan_text_for_forbidden_language(
            text="This draft must not claim lender ready status.",
            source_field="unit_test_text",
        )
        self.assertGreaterEqual(len(findings), 1)

    def test_evidence_gap_detection(self):
        gaps = detect_evidence_gaps(
            rules=[
                EvidenceRule(
                    project_area="permitting",
                    required_evidence_type="environmental_screening",
                    minimum_count=1,
                    severity_if_missing="HIGH",
                    rationale="Required evidence missing.",
                )
            ],
            observed=[
                ObservedEvidence(
                    evidence_id="fixture-1",
                    evidence_type="financial_model",
                    project_area="permitting",
                )
            ],
        )
        self.assertEqual(len(gaps), 1)


if __name__ == "__main__":
    unittest.main()
