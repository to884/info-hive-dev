"""中断の検査が欠けた試験結果を、全量試験の合格として扱わない。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'poc/rag/full_ann'))
from common import REQUIRED_CHECKS, validate_checks


class HarnessTests(unittest.TestCase):
    def test_missing_interruption_evidence_is_rejected(self):
        rows = [{'name': name, 'passed': True} for name in REQUIRED_CHECKS
                if name != 'ann_update_interrupt_stop_boundary_verified']
        with self.assertRaisesRegex(RuntimeError, 'ann_update_interrupt_stop_boundary_verified'):
            validate_checks(rows)

    def test_failed_check_is_not_hidden_by_a_later_pass(self):
        rows = [{'name': name, 'passed': True} for name in REQUIRED_CHECKS]
        rows.append({'name': 'ann_update_interrupt_stop_boundary_verified', 'passed': False})
        with self.assertRaisesRegex(RuntimeError, 'failed='):
            validate_checks(rows)

    def test_complete_evidence_is_accepted(self):
        validate_checks([{'name': name, 'passed': True} for name in REQUIRED_CHECKS])


if __name__ == '__main__':
    unittest.main()
