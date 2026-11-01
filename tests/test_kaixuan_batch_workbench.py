import tempfile
import unittest
import zipfile
from pathlib import Path

from app.kaixuan_batch_workbench import (
    BATCH_ID,
    import_archive,
    payload,
)


class DistributionWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ledger = self.root / "ledger.json"
        self.files = self.root / "files"
        self.archive = self.root / "铺货资料.zip"
        with zipfile.ZipFile(self.archive, "w") as output:
            output.writestr("10.26二店上新25个/已上传成功/圣诞印章V1.xlsm", b"uploaded")
            output.writestr("10.26二店上新25个/报价缺失/泡泡棒V1.xlsm", b"missing-price")
            output.writestr("10.26二店上新25个/冻结的/跳跳玩具V1.xlsm", b"frozen")
            output.writestr("10.26二店上新25个/气球套装V1.xlsm", b"ready")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_import_creates_three_owner_tabs_and_maps_source_groups(self):
        result = import_archive(self.archive, self.ledger, self.files)
        self.assertEqual(4, result["count"])

        data = payload(self.ledger)
        self.assertEqual(["cccady", "图图", "凯旋 · 10.26"], [batch["name"] for batch in data["batches"]])
        kaixuan = next(batch for batch in data["batches"] if batch["id"] == BATCH_ID)
        self.assertEqual(["2店"], kaixuan["stores"])
        self.assertEqual(4, len(kaixuan["rows"]))
        by_group = {row["source_group"]: row for row in kaixuan["rows"]}
        self.assertEqual("已上传", by_group["已上传成功"]["status"])
        self.assertEqual("需修正", by_group["报价缺失"]["status"])
        self.assertEqual("冻结", by_group["冻结的"]["status"])
        self.assertEqual("可上传", by_group["待上传"]["status"])
        self.assertTrue(all(row["files"]["output_file"]["exists"] for row in kaixuan["rows"]))
        self.assertEqual("圣诞印章", by_group["已上传成功"]["product_name"])

    def test_second_owner_import_preserves_kaixuan_and_keeps_filename_version(self):
        import_archive(self.archive, self.ledger, self.files)
        tutu_archive = self.root / "图图资料.zip"
        with zipfile.ZipFile(tutu_archive, "w") as output:
            output.writestr("10.26链接完整_WESSP_adult/金色皇冠V3_已改for adult.xlsm", b"tutu-v3")

        result = import_archive(
            tutu_archive,
            self.ledger,
            self.files,
            owner="图图",
            store_id="1店",
        )

        self.assertEqual("distribution-tutu-2026-10-26", result["batch_id"])
        data = payload(self.ledger)
        self.assertEqual(
            ["cccady", "图图 · 10.26", "凯旋 · 10.26"],
            [batch["name"] for batch in data["batches"]],
        )
        self.assertEqual(4, len(next(batch for batch in data["batches"] if batch["id"] == BATCH_ID)["rows"]))
        tutu = next(batch for batch in data["batches"] if batch["id"] == result["batch_id"])
        self.assertEqual(["1店"], tutu["stores"])
        self.assertEqual("金色皇冠", tutu["rows"][0]["product_name"])
        self.assertEqual(3, tutu["rows"][0]["output_versions"][-1]["version"])
        self.assertEqual("V3", tutu["rows"][0]["output_versions"][0]["label"])


if __name__ == "__main__":
    unittest.main()
