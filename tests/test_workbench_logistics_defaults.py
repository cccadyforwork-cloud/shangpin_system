import unittest

from app.logistics_defaults import apply_workbench_package_defaults


class WorkbenchLogisticsDefaultsTest(unittest.TestCase):
    def test_selected_tier_overrides_supplier_package_measurements(self):
        rows = [{
            "sku": "CHILD-1",
            "parentage_level": "Child",
            "logistics_tier": "4_8_oz",
            "shipping_fee_usd": "1.77",
            "package_length_in": "9.45",
            "package_width_in": "3.15",
            "package_height_in": "0.79",
            "package_weight_lb": "0.40",
        }]
        self.assertTrue(apply_workbench_package_defaults(rows))
        self.assertEqual(
            [rows[0][field] for field in ("package_length_in", "package_width_in", "package_height_in", "package_weight_lb")],
            ["5.91", "3.94", "1.57", "0.44"],
        )

    def test_shipping_fee_identifies_tier_and_parent_stays_empty(self):
        rows = [
            {"sku": "PARENT-1", "parentage_level": "Parent", "logistics_tier": "4_8_oz", "package_length_in": "5.91"},
            {"sku": "CHILD-1", "parentage_level": "Child", "shipping_fee_usd": "1.77", "package_length_in": "9.45"},
        ]
        self.assertTrue(apply_workbench_package_defaults(rows))
        self.assertEqual(rows[0]["logistics_tier"], "")
        self.assertEqual(rows[0]["package_length_in"], "")
        self.assertEqual(rows[1]["logistics_tier"], "4_8_oz")
        self.assertEqual(rows[1]["package_length_in"], "5.91")

    def test_without_selected_tier_or_fee_no_default_is_invented(self):
        rows = [{"sku": "CHILD-1", "package_length_in": "9.45"}]
        self.assertFalse(apply_workbench_package_defaults(rows))
        self.assertEqual(rows[0]["package_length_in"], "9.45")


if __name__ == "__main__":
    unittest.main()
