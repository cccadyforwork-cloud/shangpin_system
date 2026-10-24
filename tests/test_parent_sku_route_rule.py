import unittest
from pathlib import Path

from app.analyzer import _route_strategy, _source_parent_sku
from app.template_writer import prepare_variation_rows


class ParentSkuRouteRuleTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
