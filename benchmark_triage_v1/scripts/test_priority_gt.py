"""Protocol regression tests: optional metadata never changes eligibility or split."""
import copy
import unittest
from unittest.mock import patch

import _priority_gt as priority


class MinimalHumanGTTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"candidate_id": f"C{i}", "review_label": label}
                     for i, label in enumerate((*priority.PRIMARY, "AMBIGUOUS"))]
        self.manifest = {"priority_candidate_ids": [r["candidate_id"] for r in self.rows],
                         "priority_selected": 4, "human_label_sha256": priority.label_digest(self.rows)}

    def validate(self, rows=None, queue=None, manifest=None):
        rows = copy.deepcopy(self.rows if rows is None else rows)
        queue = copy.deepcopy(rows + [{"candidate_id": "UNREVIEWED", "review_label": ""}] if queue is None else queue)
        with patch.object(priority, "read_csv", side_effect=[rows, queue]), \
             patch.object(priority, "read_json", return_value=manifest or self.manifest), \
             patch.object(type(priority.MANIFEST), "exists", return_value=True):
            return priority.validate_labels(persist=False)

    def test_label_only_gt_passes_and_unreviewed_stays_out(self):
        result = self.validate()
        self.assertTrue(result["human_review_complete"])
        self.assertEqual(result["primary_usable"], 3)
        self.assertEqual(result["ambiguous_challenge"], 1)
        self.assertEqual(result["unreviewed"], 1)
        self.assertFalse(result["additional_human_review_required"])
        self.assertEqual(result["auxiliary_missing"]["review_confidence"], 4)

    def test_missing_label_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["review_label"] = ""
        result = self.validate(rows)
        self.assertFalse(result["human_review_complete"])
        self.assertTrue(result["additional_human_review_required"])

    def test_invalid_label_fails_without_generating_judgment(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["review_label"] = "MODEL_NORMAL"
        result = self.validate(rows)
        self.assertFalse(result["human_review_complete"])
        self.assertEqual(result["invalid_labels"], 1)

    def test_duplicate_or_foreign_id_fails(self):
        for cid in ("C1", "foreign"):
            with self.subTest(cid=cid):
                rows = copy.deepcopy(self.rows)
                rows[0]["candidate_id"] = cid
                self.assertFalse(self.validate(rows)["human_review_complete"])

    def test_manual_label_changes_fail_even_if_taxonomy_valid(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["review_label"] = "ANCHORED_DANGER"
        self.assertFalse(self.validate(rows)["human_review_complete"])

    def test_label_outside_registered_subset_fails(self):
        queue = self.rows + [{"candidate_id": "foreign", "review_label": "CLEAR_NORMAL"}]
        self.assertFalse(self.validate(queue=queue)["human_review_complete"])

    def test_split_keeps_all_classes_and_physical_groups_ignores_confidence(self):
        rows = []
        for group in range(4):
            for i, label in enumerate(priority.PRIMARY):
                rows.append({"candidate_id": f"G{group}C{i}", "review_label": label,
                             "scene_group_id": f"S{group}", "split_group_id": f"G{group}",
                             "related_to_reasoning_benchmark": "True" if group < 2 else "False",
                             "review_confidence": ""})
        assignment, _ = priority.choose_split(rows)
        changed = copy.deepcopy(list(reversed(rows)))
        for row in changed:
            row["review_confidence"] = "LOW"
            row["observable_summary"] = "optional text"
        self.assertEqual(assignment, priority.choose_split(changed)[0])
        for split in ("calibration", "test"):
            self.assertEqual(set(priority.PRIMARY), {r["review_label"] for r in rows if assignment[r["split_group_id"]] == split})


if __name__ == "__main__":
    unittest.main()
