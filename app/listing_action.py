"""Choose listing actions from the immediately preceding project template."""

from pathlib import Path
import re

from openpyxl import load_workbook

from .paths import LEGACY_FILLED_TEMPLATE_DIR
from .template_sheet import find_template_sheet, template_sheet_names_text
from .versioning import version_number


CREATE_ACTION = "Create or Replace (Full Update)"
EDIT_ACTION = "Edit (Partial Update)"
SKU_FIELD = "contribution_sku#1.value"


def previous_version_template(project_dir, output_path):
    """Find the latest lower version in this project, never the output itself."""
    current_version = _logical_version(output_path)
    if current_version < 2:
        return None
    version_dir = Path(project_dir) / LEGACY_FILLED_TEMPLATE_DIR
    candidates = [
        path for path in version_dir.glob("*")
        if path.is_file()
        and not path.name.startswith("~$")
        and path.suffix.lower() in {".xlsx", ".xlsm"}
        and path.resolve() != Path(output_path).resolve()
        and 0 < _logical_version(path) < current_version
    ]
    if not candidates:
        raise ValueError(f"生成 V{current_version} 前需要上一版填表文件，用于判断哪些 SKU 已存在：{version_dir}")
    return max(candidates, key=lambda path: (_logical_version(path), path.stat().st_mtime))


def _logical_version(path):
    stem = Path(path).stem
    # versioned_template_path appends _2 when the same version name exists.
    duplicate = re.fullmatch(r"(.+V\d+)_\d+", stem, re.I)
    return version_number(duplicate.group(1) if duplicate else stem)


def template_skus(path):
    """Read SKU identities only; the prior file's actions are irrelevant."""
    path = Path(path)
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = find_template_sheet(workbook)
        if sheet is None:
            raise ValueError(f"上一版没有 {template_sheet_names_text()} 页：{path}")
        sku_col = next(
            (col for col in range(1, sheet.max_column + 1) if sheet.cell(5, col).value == SKU_FIELD),
            None,
        )
        if sku_col is None:
            raise ValueError(f"上一版没有 SKU 字段：{path}")
        skus = {
            str(sheet.cell(row, sku_col).value).strip()
            for row in range(7, sheet.max_row + 1)
            if sheet.cell(row, sku_col).value not in (None, "")
        }
        if not skus:
            raise ValueError(f"上一版没有可比较的 SKU 数据：{path}")
        return skus
    finally:
        workbook.close()


def action_for_sku(sku, previous_skus):
    return EDIT_ACTION if str(sku or "").strip() in previous_skus else CREATE_ACTION
