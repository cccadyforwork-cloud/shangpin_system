import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from openpyxl import Workbook

from app.batch_fast_prelisting import (
    _child_sku,
    _fast_copy_fallback,
    _output_filename,
    _row_changed,
    extract_competitor_price,
    extract_competitor_variants,
    resolve_logistics_tier,
)
from app.listing_rules import validate_listing_row


class BatchFastPrelistingTest(unittest.TestCase):
    def test_resolves_le_4_oz_from_page_weight(self):
        tier = resolve_logistics_tier(weight_grams=80)
        self.assertEqual(tier["id"], "le_4_oz")
        self.assertEqual(tier["package_in"], [3.94, 3.94, 0.79])
        self.assertEqual(tier["weight_lb"], 0.22)

    def test_resolves_explicit_tier(self):
        tier = resolve_logistics_tier(tier_id="4_8_oz")
        self.assertEqual(tier["package_in"], [5.91, 3.94, 1.57])
        self.assertEqual(tier["weight_lb"], 0.44)

    def test_short_sku_generation(self):
        task = {"parent_sku": "CA-GLASSBEADS", "color": "Green", "size": "6 MM"}
        self.assertEqual(_child_sku(task, {}, 1), "CA-GLASSBEADS-GREEN6MM")

    def test_output_name_cannot_escape_output_directory(self):
        filename = _output_filename({"output_name": "../危险文件.xlsx"}, "fallback", ".xlsm")
        self.assertEqual(filename, "危险文件V1.xlsx")

    def test_fallback_copy_passes_listing_rules(self):
        copy = _fast_copy_fallback({
            "product_name": "Glass Beads",
            "color": "Green",
            "size": "6 MM",
            "material": "Glass",
            "set_count": 100,
        })
        self.assertEqual(validate_listing_row(copy), [])

    def test_extracts_complete_single_color_twister_without_asins(self):
        html = '''
        <input name="twisterDimKeys" value="color_name"/>
        <li id="color_name_0" title="Click to select Blue" data-csa-c-item-id="ASIN1"></li>
        <li id="color_name_1" title="Click to select Llight Blue" data-csa-c-item-id="ASIN2"></li>
        <li id="color_name_2" title="Click to select Green" data-csa-c-item-id="ASIN3"></li>
        '''
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "competitor.html"
            path.write_text(html, encoding="utf-8")
            variants = extract_competitor_variants([path])
        self.assertEqual(variants, [
            {"color": "Blue"},
            {"color": "Light Blue"},
            {"color": "Green"},
        ])
        self.assertTrue(all("asin" not in variant for variant in variants))

    def test_does_not_auto_expand_combined_twister(self):
        html = '''
        <input name="twisterDimKeys" value="color_name,size_name"/>
        <li id="color_name_0" title="Click to select Blue"></li>
        '''
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "competitor.html"
            path.write_text(html, encoding="utf-8")
            self.assertEqual(extract_competitor_variants([path]), [])

    def test_extracts_current_price_not_discount_amount(self):
        html = '''
        <span class="aok-offscreen"> $1.95 </span>
        <span class="a-price priceToPay"><span class="a-offscreen"></span></span>
        <span>Includes $1.96 Amazon discount</span>
        '''
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "competitor.html"
            path.write_text(html, encoding="utf-8")
            self.assertEqual(extract_competitor_price([path]), 1.95)

    def test_row_change_detection_ignores_action_only(self):
        ws = Workbook().active
        ws.cell(1, 1).value = "Same Title"
        ws.cell(1, 2).value = "Edit (Partial Update)"
        fields = {"item_name": 1, "::record_action": 2}
        previous = {"item_name": "Same Title"}
        self.assertFalse(_row_changed(ws, 1, fields, previous))
        ws.cell(1, 1).value = "Updated Title"
        self.assertTrue(_row_changed(ws, 1, fields, previous))


if __name__ == "__main__":
    unittest.main()
