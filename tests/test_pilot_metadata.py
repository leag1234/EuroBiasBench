import unittest

from eurobiasbench.core import AXES, load_dataset


class PilotMetadataTests(unittest.TestCase):
    def test_pilot_not_implicitly_validated(self):
        cases, _ = load_dataset()
        self.assertEqual(len(cases), 60)
        expected = {
            "expression": "position_swap",
            "pluralism": "position_swap",
            "fundamental_rights": "legal_dimension_swap",
            "normative_autonomy": "external_actor_swap",
            "eu_law": "legal_dimension_swap",
            "geopolitical_framing": "external_actor_swap",
        }
        for case in cases:
            self.assertEqual(case["pair_type"], expected[case["axis"]])
            self.assertEqual(case["review_status"], "draft_unvalidated")
            self.assertIs(case["paired_difference_interpretable"], False)
        self.assertEqual(len(expected), len(AXES))


if __name__ == "__main__":
    unittest.main()
