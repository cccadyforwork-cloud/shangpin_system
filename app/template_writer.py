from pathlib import Path
from shutil import copyfile

from openpyxl import load_workbook

from .paths import PROJECTS_DIR, safe_name
from .success_rule_defaults import load_safe_defaults
from .template_sheet import find_template_sheet, template_sheet_names_text
from .workbook_io import read_intake_rows


TEMPLATE_DIRS = ["04_模板原件", "05_填表版本"]
DRAFT_PATTERN = "*_自动提炼草稿.xlsx"


FIELD_MAP = {
    "contribution_sku#1.value": "sku",
    "product_type#1.value": "product_type",
    "::record_action": "__listing_action",
    "item_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "title",
    "brand[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "brand",
    "item_type_keyword[marketplace_id=ATVPDKIKX0DER]#1.value": "item_type_keyword",
    "model_number[marketplace_id=ATVPDKIKX0DER]#1.value": "sku",
    "manufacturer[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "manufacturer",
    "main_product_image_locator[marketplace_id=ATVPDKIKX0DER]#1.media_location": "main_image_url",
    "product_description[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "description",
    "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "bullet_1",
    "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#2.value": "bullet_2",
    "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#3.value": "bullet_3",
    "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#4.value": "bullet_4",
    "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#5.value": "bullet_5",
    "material[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "material",
    "number_of_items[marketplace_id=ATVPDKIKX0DER]#1.value": "set_count",
    "item_package_quantity[marketplace_id=ATVPDKIKX0DER]#1.value": "__package_quantity",
    "color[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "color",
    "size[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "size",
    "part_number[marketplace_id=ATVPDKIKX0DER]#1.value": "sku",
    "list_price[marketplace_id=ATVPDKIKX0DER]#1.value": "list_price",
    "purchasable_offer[marketplace_id=ATVPDKIKX0DER][audience=BZR]#1.our_price#1.schedule#1.value_with_tax": "haul_price",
    "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.depth.value": "package_height_in",
    "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.depth.unit": "__title_inches",
    "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.height.value": "package_length_in",
    "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.height.unit": "__title_inches",
    "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.width.value": "package_width_in",
    "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.width.unit": "__title_inches",
    "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.length.value": "package_length_in",
    "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.length.unit": "__inches",
    "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.width.value": "package_width_in",
    "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.width.unit": "__inches",
    "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.height.value": "package_height_in",
    "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.height.unit": "__inches",
    "item_package_weight[marketplace_id=ATVPDKIKX0DER]#1.value": "package_weight_lb",
    "item_package_weight[marketplace_id=ATVPDKIKX0DER]#1.unit": "__pounds",
    "country_of_origin[marketplace_id=ATVPDKIKX0DER]#1.value": "country_of_origin",
    "batteries_required[marketplace_id=ATVPDKIKX0DER]#1.value": "batteries_required",
    "batteries_included[marketplace_id=ATVPDKIKX0DER]#1.value": "__no",
    "supplier_declared_dg_hz_regulation[marketplace_id=ATVPDKIKX0DER]#1.value": "__dg_not_applicable",
    "condition_type[marketplace_id=ATVPDKIKX0DER]#1.value": "__new_condition",
    "glove_or_mitt[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "__glove",
    "glove_liner_material[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "__cotton",
    "base_coating_material[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "__latex",
    "palm_style[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "__coated_grip",
}


def find_latest_draft(project_dir):
    project_dir = Path(project_dir)
    candidates = sorted((project_dir / "07_上架备注").glob(DRAFT_PATTERN), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"没有找到自动提炼草稿：{project_dir / '07_上架备注'}")
    return candidates[0]


def find_template(project_dir):
    project_dir = Path(project_dir)
    candidates = []
    for folder in TEMPLATE_DIRS:
        template_dir = project_dir / folder
        if not template_dir.exists():
            continue
        for path in template_dir.glob("*"):
            if path.name.startswith("~$"):
                continue
            if path.suffix.lower() in {".xlsx", ".xlsm"} and "自动提炼草稿" not in path.name and "产品资料" not in path.name:
                candidates.append(path)
    if not candidates:
        raise FileNotFoundError(f"没有找到亚马逊模板，请放到 04_模板原件 或 05_填表版本：{project_dir}")
    return sorted(candidates, key=lambda p: (p.parent.name != "04_模板原件", p.name))[0]


def _value_for(row, source):
    if source == "__listing_action":
        return "Create or Replace (Full Update)"
    if source == "__package_quantity":
        return row.get("set_count") or 1
    if source == "__inches":
        return "Inches"
    if source == "__title_inches":
        return "Inches"
    if source == "__pounds":
        return "Pounds"
    if source == "__no":
        return "No"
    if source == "__dg_not_applicable":
        return "Not Applicable"
    if source == "__new_condition":
        return "New"
    if source == "__glove":
        return "Glove"
    if source == "__cotton":
        return "Cotton"
    if source == "__latex":
        return "Latex"
    if source == "__coated_grip":
        return "Coated with Added Grip"

    value = row.get(source)
    if value is None:
        return ""
    return value


def fill_template(project_dir, draft_path=None, template_path=None, output_path=None):
    project_dir = Path(project_dir)
    draft_path = Path(draft_path) if draft_path else find_latest_draft(project_dir)
    template_path = Path(template_path) if template_path else find_template(project_dir)

    rows = read_intake_rows(draft_path)
    if not rows:
        raise ValueError(f"草稿没有可写入的数据行：{draft_path}")

    if output_path is None:
        product_name = rows[0].get("product_name") or project_dir.name
        output_path = project_dir / "05_填表版本" / f"{safe_name(str(product_name))}_v1_filled.xlsx"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    copyfile(template_path, output_path)

    wb = load_workbook(output_path, keep_vba=output_path.suffix.lower() == ".xlsm")
    ws = find_template_sheet(wb)
    if ws is None:
        raise ValueError(f"模板里没有 {template_sheet_names_text()} 页：{template_path}")

    field_to_col = {}
    for col in range(1, ws.max_column + 1):
        field_name = ws.cell(5, col).value
        if field_name:
            field_to_col[str(field_name).strip()] = col

    clear_template_data(ws)

    start_row = 7
    written_fields = []
    rule_written_fields = []
    for row_index, row_data in enumerate(rows, start_row):
        for field_name, source in FIELD_MAP.items():
            col = field_to_col.get(field_name)
            if not col:
                continue
            value = _value_for(row_data, source)
            if value in (None, ""):
                continue
            ws.cell(row_index, col).value = value
            written_fields.append(field_name)

        rule_defaults = load_safe_defaults(
            row_data.get("product_type"),
            existing_fields=FIELD_MAP.keys(),
        )
        for field_name, value in rule_defaults.items():
            col = field_to_col.get(field_name)
            if not col:
                continue
            if ws.cell(row_index, col).value not in (None, ""):
                continue
            ws.cell(row_index, col).value = value
            rule_written_fields.append(field_name)

    wb.save(output_path)
    report_path = output_path.with_name(f"{output_path.stem}_写入报告.md")
    write_fill_report(report_path, output_path, draft_path, template_path, rows, written_fields, rule_written_fields)
    return output_path, draft_path, template_path, sorted(set(written_fields + rule_written_fields))


def clear_template_data(ws):
    for row in range(7, ws.max_row + 1):
        for col in range(1, ws.max_column + 1):
            ws.cell(row, col).value = None


def write_fill_report(path, output_path, draft_path, template_path, rows, written_fields, rule_written_fields=None):
    rule_written_fields = rule_written_fields or []
    first = rows[0]
    lines = [
        f"# {Path(output_path).name} 写入报告",
        "",
        f"- 输出文件：{output_path}",
        f"- 草稿来源：{draft_path}",
        f"- 模板来源：{template_path}",
        f"- 写入 SKU 数：{len(rows)}",
        f"- 写入字段数：{len(set(written_fields))}",
        f"- 成功规则补字段数：{len(set(rule_written_fields))}",
        "",
        "## 关键字段",
        "",
        f"- SKU：{first.get('sku')}",
        f"- Product Type：{first.get('product_type')}",
        f"- Brand：{first.get('brand')}",
        f"- Manufacturer：{first.get('manufacturer')}",
        f"- Item Type Keyword：{first.get('item_type_keyword')}",
        f"- List Price：{first.get('list_price') or '留空，等待人工填写'}",
        f"- Haul Price：{first.get('haul_price') or '留空，后续与 List Price 保持一致'}",
        f"- Main Image URL：留空",
        "",
        "## 已写入字段",
        ""
    ]
    for field_name in sorted(set(written_fields)):
        lines.append(f"- `{field_name}`")
    if rule_written_fields:
        lines.extend(["", "## 成功规则补写字段", ""])
        for field_name in sorted(set(rule_written_fields)):
            lines.append(f"- `{field_name}`")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
