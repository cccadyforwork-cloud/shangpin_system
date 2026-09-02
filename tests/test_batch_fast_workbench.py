import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from openpyxl import Workbook

from app.batch_fast_workbench import (
    attach_file,
    build_output_archive,
    import_sheets,
    load_ledger,
    package_shared_data,
    payload,
    referenced_file,
    save_ledger,
    update_row,
)


class BatchFastWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ledger = self.root / "ledger.json"
        self.files = self.root / "files"
        self.html = self.root / "B0ABCDEFGH.html"
        self.html.write_text("<html></html>", encoding="utf-8")
        self.sheet = self.root / "2店批量上品.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["LINK", "竞品HTML", "模版表格"])
        sheet.append(["https://www.amazon.com/dp/B0ABCDEFGH", str(self.html), ""])
        workbook.save(self.sheet)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_import_update_and_reimport_preserve_row_state(self):
        data = import_sheets([self.sheet], self.ledger)
        batch_id = data["batches"][0]["id"]
        update_row(batch_id, "B0ABCDEFGH", {"status": "待复核", "note": "预估价格"}, self.ledger)
        import_sheets([self.sheet], self.ledger)
        rendered = payload(self.ledger)
        row = rendered["batches"][0]["rows"][0]
        self.assertEqual("待复核", row["status"])
        self.assertEqual("预估价格", row["note"])
        self.assertTrue(row["files"]["competitor_html"]["exists"])

    def test_upload_output_and_secure_file_resolution(self):
        data = import_sheets([self.sheet], self.ledger)
        batch_id = data["batches"][0]["id"]
        target, row = attach_file(
            batch_id,
            "B0ABCDEFGH",
            "output_file",
            "输出V1.xlsm",
            io.BytesIO(b"test workbook"),
            self.ledger,
            self.files,
        )
        self.assertEqual(str(target.resolve()), row["output_file"])
        self.assertEqual(target.resolve(), referenced_file(target, self.ledger, self.files))
        outside = self.root / "outside.txt"
        outside.write_text("private", encoding="utf-8")
        self.assertIsNone(referenced_file(outside, self.ledger, self.files))

    def test_rejects_non_spreadsheet_template_value(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["LINK", "竞品HTML", "模版表格"])
        sheet.append(["https://www.amazon.com/dp/B0ABCDEFGH", str(self.html), str(self.html)])
        workbook.save(self.sheet)
        data = import_sheets([self.sheet], self.ledger)
        self.assertEqual("", data["batches"][0]["rows"][0]["source_template"])

    def test_builds_zip_from_available_batch_outputs(self):
        data = import_sheets([self.sheet], self.ledger)
        batch_id = data["batches"][0]["id"]
        target, _row = attach_file(
            batch_id,
            "B0ABCDEFGH",
            "output_file",
            "输出V1.xlsm",
            io.BytesIO(b"test workbook"),
            self.ledger,
            self.files,
        )
        filename, archive_bytes, count = build_output_archive(batch_id, self.ledger)
        self.assertEqual("2店批量上品_输出文档.zip", filename)
        self.assertEqual(1, count)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            self.assertEqual([target.name], archive.namelist())
            self.assertEqual(b"test workbook", archive.read(target.name))

    def test_new_output_version_becomes_current_and_keeps_v1_downloadable(self):
        data = import_sheets([self.sheet], self.ledger)
        batch_id = data["batches"][0]["id"]
        v1, _row = attach_file(
            batch_id,
            "B0ABCDEFGH",
            "output_file",
            "测试产品V1.xlsm",
            io.BytesIO(b"version one"),
            self.ledger,
            self.files,
        )
        v2, row = attach_file(
            batch_id,
            "B0ABCDEFGH",
            "output_file",
            "测试产品V2.xlsm",
            io.BytesIO(b"version two"),
            self.ledger,
            self.files,
        )
        self.assertEqual(str(v2.resolve()), row["output_file"])
        rendered_row = payload(self.ledger)["batches"][0]["rows"][0]
        self.assertEqual(["V2", "V1"], [item["label"] for item in rendered_row["output_versions"]])
        self.assertTrue(rendered_row["output_versions"][0]["current"])
        self.assertEqual(v1.resolve(), referenced_file(v1, self.ledger, self.files))

        _filename, archive_bytes, count = build_output_archive(batch_id, self.ledger)
        self.assertEqual(1, count)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            self.assertEqual([v2.name], archive.namelist())
            self.assertEqual(b"version two", archive.read(v2.name))

    def test_store_views_share_competitor_but_keep_downstream_files_independent(self):
        data = import_sheets([self.sheet], self.ledger)
        batch = data["batches"][0]
        batch["stores"] = ["1店", "2店"]
        batch["rows"][0]["store_id"] = "1店"
        save_ledger(data, self.ledger)

        data = import_sheets([self.sheet], self.ledger)
        rows = data["batches"][0]["rows"]
        store_1 = next(row for row in rows if row["store_id"] == "1店")
        store_2 = next(row for row in rows if row["store_id"] == "2店")
        self.assertEqual(store_1["link"], store_2["link"])
        self.assertEqual(store_1["competitor_html"], store_2["competitor_html"])
        self.assertEqual("", store_2["source_template"])
        self.assertEqual("", store_2["output_file"])
        self.assertEqual("待处理", store_2["status"])
        self.assertEqual(1, payload(self.ledger)["totals"]["rows"])

        packaged = package_shared_data(self.ledger, self.files, self.root / "source_sheets")
        self.assertEqual([], packaged["missing"])
        packaged_rows = load_ledger(self.ledger)["batches"][0]["rows"]
        self.assertEqual(packaged_rows[0]["competitor_html"], packaged_rows[1]["competitor_html"])

        attach_file(
            batch["id"],
            store_2["id"],
            "output_file",
            "二店输出V1.xlsm",
            io.BytesIO(b"store two"),
            self.ledger,
            self.files,
        )
        filename, archive_bytes, count = build_output_archive(batch["id"], self.ledger, store_id="2店")
        self.assertEqual("2店批量上品_2店_输出文档.zip", filename)
        self.assertEqual(1, count)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            self.assertEqual(["二店输出V1.xlsm"], archive.namelist())


if __name__ == "__main__":
    unittest.main()
