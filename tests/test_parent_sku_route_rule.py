import unittest
from pathlib import Path

from app.analyzer import _route_strategy, _source_parent_sku
from app.template_writer import prepare_variation_rows


class ParentSkuRouteRuleTest(unittest.TestCase):
    def test_default_generated_parent_and_children_use_new_business_rule(self):
        rows = [
            {"product_name": "Mop Pad Extra", "store_id": "1店", "route": "Haul Generic Variation", "color": "Pink", "set_count": 2, "variation_theme": "COLOR/NUMBER_OF_ITEMS"},
            {"product_name": "Mop Pad Extra", "store_id": "1店", "route": "Haul Generic Variation", "color": "Green+White", "set_count": 4, "variation_theme": "COLOR/NUMBER_OF_ITEMS"},
        ]
        prepared = prepare_variation_rows(rows, Path("/tmp/mop_pad"))
        self.assertEqual([row["sku"] for row in prepared], [
            "TTCA-MopPad",
            "TTCA-MopPad-Pink-2P",
            "TTCA-MopPad-GreenWhite-4P",
        ])

    def test_source_parent_sku_overrides_single_route(self):
        source = [(Path("SKU定价.csv"), "SKU,角色,是否当前必需\nPARENT-1,parent,否\nCHILD-1,child,是\n")]
        parent_sku = _source_parent_sku(source)
        self.assertEqual(parent_sku, "PARENT-1")
        self.assertEqual(_route_strategy("", "Haul Generic", 1, 1, route_mode="single_child", parent_sku=parent_sku), "variation")

    def test_explicit_parent_sku_creates_parent_even_with_single_route(self):
        rows = [{
            "product_name": "Kitchen Shears",
            "route": "Haul Generic",
            "sku": "CHILD-1",
            "parent_sku": "PARENT-1",
            "color": "Silver",
            "title": "Kitchen Shears, Silver",
        }]
        prepared = prepare_variation_rows(rows, Path("/tmp/kitchen_shears"))
        self.assertEqual([row["sku"] for row in prepared], ["PARENT-1", "CHILD-1"])
        self.assertEqual([row["parentage_level"] for row in prepared], ["Parent", "Child"])
        self.assertTrue(all(row["route"] == "Haul Generic Variation" for row in prepared))

    def test_existing_parent_makes_unmarked_sku_a_child(self):
        rows = [
            {"sku": "PARENT-1", "parentage_level": "Parent", "route": "Haul Generic"},
            {"sku": "CHILD-1", "route": "Haul Generic", "color": "Silver"},
        ]
        prepared = prepare_variation_rows(rows, Path("/tmp/kitchen_shears"))
        self.assertEqual(prepared[1]["parentage_level"], "Child")
        self.assertEqual(prepared[1]["parent_sku"], "PARENT-1")
        self.assertTrue(all(row["route"] == "Haul Generic Variation" for row in prepared))

    def test_set_name_variants_do_not_leak_first_child_fields_to_parent(self):
        rows = [
            {
                "product_name": "Espresso Spoon",
                "store_id": "2店",
                "route": "Haul Generic Variation",
                "variation_theme": "SET_NAME",
                "set_name": "Style 06",
                "set_count": 2,
                "unit_count": 2,
                "title": "2 Piece Stainless Steel Spoon Set, Style 06",
            },
            {
                "product_name": "Espresso Spoon",
                "store_id": "2店",
                "route": "Haul Generic Variation",
                "variation_theme": "SET_NAME",
                "set_name": "Wood Handle Set",
                "set_count": 3,
                "unit_count": 3,
                "title": "3 Piece Stainless Steel Spoon Set, Wood Handle Set",
            },
        ]
        prepared = prepare_variation_rows(rows, Path("/tmp/espresso_spoon"))
        parent = prepared[0]
        self.assertEqual(parent["sku"], "CA-EspressoSpoon")
        self.assertEqual(parent["set_name"], "")
        self.assertEqual(parent["set_count"], "")
        self.assertEqual(parent["unit_count"], "")
        self.assertNotIn("Style 06", parent["title"])
        self.assertNotIn("Wood Handle Set", parent["title"])


if __name__ == "__main__":
    unittest.main()
