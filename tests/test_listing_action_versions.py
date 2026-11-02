from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import Workbook, load_workbook

from app.template_writer import fill_template
from app.listing_action import _logical_version
from app.workbook_io import write_intake_workbook


class ListingActionVersionTest(unittest.TestCase):
    def test_duplicate_filename_keeps_its_logical_version(self):
        self.assertEqual(_logical_version("猫玩具V5_2.xlsm"), 5)

    def test_only_skus_new_to_the_previous_version_are_created(self):
        with TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source = project / "source.xlsx"
            draft = project / "draft.xlsx"
            versions = project / "05_填表版本"
            versions.mkdir()
            workbook = Workbook()
            ws = workbook.active
            ws.title = "Template"
            for col, name in enumerate((
                "contribution_sku#1.value",
                "::record_action",
                "parentage_level[marketplace_id=ATVPDKIKX0DER]#1.value",
            ), 1):
                ws.cell(5, col).value = name
            workbook.save(source)

            def draft_rows(child_skus):
                rows = [{
                    "project_name": "猫玩具", "product_name": "猫玩具", "route": "Haul Generic Variation",
                    "sku": "PARENT", "parentage_level": "Parent", "title": "Cat Toy",
                }]
                rows.extend({
                    "project_name": "猫玩具", "product_name": "猫玩具", "route": "Haul Generic Variation",
                    "sku": sku, "parent_sku": "PARENT", "parentage_level": "Child", "title": "Cat Toy",
                } for sku in child_skus)
                write_intake_workbook(draft, rows)

            draft_rows(["OLD"])
            v1 = versions / "猫玩具V1.xlsx"
            fill_template(project, draft_path=draft, template_path=source, output_path=v1)
            draft_rows(["OLD", "NEW"])
            v2 = versions / "猫玩具V2.xlsx"
            fill_template(project, draft_path=draft, template_path=source, output_path=v2)

            sheet = load_workbook(v2, read_only=True, data_only=True)["Template"]
            actions = {sheet.cell(row, 1).value: sheet.cell(row, 2).value for row in range(7, 10)}
            self.assertEqual(actions, {
                "PARENT": "Edit (Partial Update)",
                "OLD": "Edit (Partial Update)",
                "NEW": "Create or Replace (Full Update)",
            })

    def test_later_version_requires_a_previous_sku_baseline(self):
        with TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source = project / "source.xlsx"
            draft = project / "draft.xlsx"
            workbook = Workbook()
            workbook.active.title = "Template"
            workbook.active.cell(5, 1).value = "contribution_sku#1.value"
            workbook.save(source)
            write_intake_workbook(draft, [{"sku": "OLD", "route": "Haul Generic"}])
            with self.assertRaisesRegex(ValueError, "上一版填表文件"):
                fill_template(project, draft_path=draft, template_path=source,
                              output_path=project / "05_填表版本" / "猫玩具V2.xlsx")


if __name__ == "__main__":
    unittest.main()
