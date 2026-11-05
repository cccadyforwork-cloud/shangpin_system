import unittest
from pathlib import Path

from app.template_writer import prepare_variation_rows
from app.template_validator import _validate_variation_titles


class VariationTitleRulesTest(unittest.TestCase):
    def test_prepare_variation_rows_generates_parent_and_preserves_child_titles(self):
        rows = [
            {
                "product_name": "Floral Card Holder Picks",
                "route": "Haul Generic Variation",
                "sku": "FLORAL-GOLD",
                "color": "Gold",
                "set_count": "50pcs 2set",
                "title": "Floral Card Holder Picks, Flower Bouquet Card Sticks for Gift Cards and Table Centerpieces, Gold",
            },
            {
                "product_name": "Floral Card Holder Picks",
                "route": "Haul Generic Variation",
                "sku": "FLORAL-SILVER",
                "color": "Silver",
                "set_count": "50pcs 2set",
                "title": "Floral Card Holder Picks, Flower Bouquet Card Sticks for Gift Cards and Table Centerpieces, Silver",
            },
        ]

        prepared = prepare_variation_rows(rows, Path("/tmp/floral_card_holder"))

        parent = prepared[0]
        children = prepared[1:]
        self.assertEqual(parent["parentage_level"], "Parent")
        self.assertTrue(parent["title"].startswith("50 Pcs 2 Set "))
        self.assertNotIn("Multiple Colors Available", parent["title"])
        self.assertNotIn("Gold", parent["title"])
        self.assertLessEqual(len(parent["title"]), 75)

        self.assertEqual(children[0]["title"], rows[0]["title"])
        self.assertEqual(children[1]["title"], rows[1]["title"])

    def test_variation_title_self_check_does_not_require_display_name_in_child_title(self):
        row_infos = {
            7: {
                "row": 7,
                "sku": "PARENT",
                "parentage": "Parent",
                "parent_sku": "",
                "variation_theme": "Color",
                "title": "Floral Card Holder Picks, Gold",
                "color": "",
                "size": "",
            },
            8: {
                "row": 8,
                "sku": "CHILD-GOLD",
                "parentage": "Child",
                "parent_sku": "PARENT",
                "variation_theme": "Color",
                "title": "Floral Card Holder Picks, Multiple Colors Available",
                "color": "Gold",
                "size": "",
            },
            9: {
                "row": 9,
                "sku": "CHILD-SILVER",
                "parentage": "Child",
                "parent_sku": "PARENT",
                "variation_theme": "Color",
                "title": "Floral Card Holder Picks, Silver",
                "color": "Silver",
                "size": "",
            },
        }

        findings = []
        _validate_variation_titles(findings, row_infos)
        messages = "\n".join(item["message"] for item in findings)

        self.assertNotIn("多颜色 Parent", messages)
        self.assertIn("Child 行，但标题包含父体总结词", messages)
        self.assertNotIn("颜色变体 Child，但标题未包含自身颜色", messages)

    def test_existing_titles_are_preserved_when_display_names_change(self):
        rows = [
            {"parentage_level": "Parent", "sku": "PARENT", "title": "Existing parent title"},
            {"parentage_level": "Child", "sku": "CHILD", "title": "Existing child title", "color": "Natural Sisal"},
        ]
        from app.variation_title_rules import apply_variation_title_rules

        prepared = apply_variation_title_rules(rows)
        self.assertEqual(prepared[0]["title"], "Existing parent title")
        self.assertEqual(prepared[1]["title"], "Existing child title")


if __name__ == "__main__":
    unittest.main()
