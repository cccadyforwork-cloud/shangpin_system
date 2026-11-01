from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import Workbook, load_workbook

from app.template_validator import FIELD_NAMES, validate_template_file
from app.template_writer import fill_template
from app.workbook_io import write_intake_workbook


MODEL_NAME_FIELD = "model_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value"


def _template(path, model_name_field=MODEL_NAME_FIELD):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Template"
    for column, name in enumerate((FIELD_NAMES["sku"], "product_type#1.value", model_name_field), 1):
        sheet.cell(5, column).value = name
    workbook.save(path)


class ModelNameSkuRuleTest(unittest.TestCase):
    def test_all_listing_routes_use_sku_as_model_name(self):
        routes = ("Haul Generic", "Haul Generic Variation", "Haul Generic Set Bundle", "Brand")
        for route in routes:
            with self.subTest(route=route), TemporaryDirectory() as temp_dir:
                project_dir = Path(temp_dir)
                draft = project_dir / "draft.xlsx"
                source = project_dir / "source.xlsx"
                output = project_dir / "filled.xlsx"
                write_intake_workbook(draft, [{
                    "project_name": "项目",
                    "product_name": "中文产品名",
                    "route": route,
                    "product_type": "ANIMAL_COLLAR",
                    "sku": "CA-TEST-001",
                    "title": "Pet Collar",
                }])
                _template(source)

                fill_template(project_dir, draft_path=draft, template_path=source, output_path=output)

                sheet = load_workbook(output, read_only=True, data_only=True)["Template"]
                sku_and_model = [(sheet.cell(row, 1).value, sheet.cell(row, 3).value)
                                 for row in range(7, sheet.max_row + 1) if sheet.cell(row, 1).value]
                self.assertIn(("CA-TEST-001", "CA-TEST-001"), sku_and_model)
                self.assertTrue(all(model in (None, sku) for sku, model in sku_and_model))

    def test_validator_rejects_model_name_different_from_sku(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.xlsx"
            _template(path)
            workbook = load_workbook(path)
            sheet = workbook["Template"]
            sheet.cell(7, 1).value = "CA-TEST-001"
            sheet.cell(7, 3).value = "中文产品名"
            workbook.save(path)

            findings, _ = validate_template_file(path)

            self.assertTrue(any(item["field"] == "Model Name" and item["severity"] == "error" for item in findings))

    def test_short_model_name_field_uses_same_rule(self):
        with TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            draft = project_dir / "draft.xlsx"
            source = project_dir / "source.xlsx"
            output = project_dir / "filled.xlsx"
            write_intake_workbook(draft, [{
                "project_name": "项目", "product_name": "中文产品名",
                "route": "Haul Generic Set Bundle", "sku": "CA-TEST-001",
                "title": "Pet Toy",
            }])
            _template(source, "model_name#1.value")

            fill_template(project_dir, draft_path=draft, template_path=source, output_path=output)

            sheet = load_workbook(output, read_only=True, data_only=True)["Template"]
            self.assertEqual(sheet.cell(7, 3).value, "CA-TEST-001")


if __name__ == "__main__":
    unittest.main()
