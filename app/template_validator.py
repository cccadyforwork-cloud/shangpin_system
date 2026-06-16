from pathlib import Path

from openpyxl import load_workbook

from .paths import OUTPUTS_DIR


FIELD_NAMES = {
    "sku": "contribution_sku#1.value",
    "skip_offer": "skip_offer[marketplace_id=ATVPDKIKX0DER]#1.value",
    "condition": "condition_type[marketplace_id=ATVPDKIKX0DER]#1.value",
    "list_price": "list_price[marketplace_id=ATVPDKIKX0DER]#1.value",
    "haul_price": "purchasable_offer[marketplace_id=ATVPDKIKX0DER][audience=BZR]#1.our_price#1.schedule#1.value_with_tax",
    "item_depth": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.depth.value",
    "item_depth_unit": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.depth.unit",
    "item_height": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.height.value",
    "item_height_unit": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.height.unit",
    "item_width": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.width.value",
    "item_width_unit": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.width.unit",
}


PRODUCT_TYPE_CONDITIONAL_FIELDS = {
    "PROTECTIVE_GLOVE": {
        "Model Name": "model_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Style": "style[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Department Name": "department[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Age Range Description": "age_range_description[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Fabric Type": "fabric_type[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Fit Type": "fit_type[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Import Designation": "import_designation[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
        "Item Thickness Decimal Value": "item_thickness[marketplace_id=ATVPDKIKX0DER]#1.decimal_value",
        "Item Thickness": "item_thickness[marketplace_id=ATVPDKIKX0DER]#1.string_value",
        "Item Thickness Unit": "item_thickness[marketplace_id=ATVPDKIKX0DER]#1.unit",
        "Warranty Description": "warranty_description[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    }
}


def validate_template_file(path, output_path=None):
    path = Path(path)
    wb = load_workbook(path, data_only=True, read_only=True)
    if "Template" not in wb.sheetnames:
        raise ValueError(f"文件没有 Template 页：{path}")
    ws = wb["Template"]
    field_to_col = {
        str(ws.cell(5, col).value).strip(): col
        for col in range(1, ws.max_column + 1)
        if ws.cell(5, col).value
    }

    findings = []
    data_rows = []
    sku_col = field_to_col.get(FIELD_NAMES["sku"])
    if not sku_col:
        findings.append(error("-", "SKU", "找不到 SKU 字段列。", "确认第 5 行字段名没有被改动。"))
    else:
        for row in range(7, ws.max_row + 1):
            if ws.cell(row, sku_col).value not in (None, ""):
                data_rows.append(row)

    condition_col = field_to_col.get(FIELD_NAMES["condition"])
    skip_offer_col = field_to_col.get(FIELD_NAMES["skip_offer"])
    list_price_col = field_to_col.get(FIELD_NAMES["list_price"])
    haul_price_col = field_to_col.get(FIELD_NAMES["haul_price"])
    product_type_col = field_to_col.get("product_type#1.value")
    dimension_pairs = [
        ("Item Depth", field_to_col.get(FIELD_NAMES["item_depth"]), field_to_col.get(FIELD_NAMES["item_depth_unit"])),
        ("Item Height", field_to_col.get(FIELD_NAMES["item_height"]), field_to_col.get(FIELD_NAMES["item_height_unit"])),
        ("Item Width", field_to_col.get(FIELD_NAMES["item_width"]), field_to_col.get(FIELD_NAMES["item_width_unit"])),
    ]
    available_dimension_pairs = [pair for pair in dimension_pairs if pair[1] and pair[2]]

    for row in data_rows:
        sku = ws.cell(row, sku_col).value
        if condition_col:
            condition = ws.cell(row, condition_col).value
            if condition != "New":
                findings.append(error(row, "Item Condition", f"{sku} 的 Item Condition 不是 New，当前为 `{condition}`。", "新品统一填写 New。"))
        else:
            findings.append(error(row, "Item Condition", "模板中找不到 Item Condition 字段。", "确认模板是否包含 condition_type 字段。"))

        if skip_offer_col:
            skip_offer = ws.cell(row, skip_offer_col).value
            if skip_offer not in (None, ""):
                findings.append(error(row, "Skip Offer", f"{sku} 的 Skip Offer 应留空，当前为 `{skip_offer}`。", "不要填写 skip_offer，让报价随价格字段正常生成。"))

        if list_price_col and haul_price_col:
            list_price = ws.cell(row, list_price_col).value
            haul_price = ws.cell(row, haul_price_col).value
            if list_price in (None, ""):
                findings.append(error(row, "List Price", f"{sku} 的 List Price 为空。", "上传前填写数字价格。"))
            if haul_price in (None, ""):
                findings.append(error(row, "Haul Price", f"{sku} 的 Haul Price 为空。", "Haul/BZR 价格应与 List Price 同步。"))

        for label, value_col, unit_col in available_dimension_pairs:
            value = ws.cell(row, value_col).value
            unit = ws.cell(row, unit_col).value
            if value not in (None, "") and unit in (None, ""):
                findings.append(error(row, f"{label} Unit", f"{sku} 的 {label} 有数值但单位为空。", "尺寸数值和单位必须成对填写。"))
            if value in (None, "") and unit not in (None, ""):
                findings.append(error(row, label, f"{sku} 的 {label} 单位有值但数值为空。", "尺寸数值和单位必须成对填写。"))

        if product_type_col:
            product_type = ws.cell(row, product_type_col).value
            for label, field_name in PRODUCT_TYPE_CONDITIONAL_FIELDS.get(str(product_type), {}).items():
                col = field_to_col.get(field_name)
                if not col:
                    continue
                value = ws.cell(row, col).value
                if value in (None, ""):
                    findings.append(error(row, label, f"{sku} 的 {label} 为空。", f"{product_type} 模板上传前应补齐该条件必填字段。"))

    if output_path is None:
        output_path = OUTPUTS_DIR / f"{path.stem}_模板自检报告.md"
    else:
        output_path = Path(output_path)
    write_report(output_path, path, findings, data_rows)
    return findings, output_path


def error(row, field, message, fix):
    return {
        "severity": "error",
        "row": row,
        "field": field,
        "message": message,
        "fix": fix,
    }


def write_report(path, checked_file, findings, data_rows):
    errors = sum(1 for item in findings if item["severity"] == "error")
    lines = [
        f"# {Path(checked_file).name} 模板自检报告",
        "",
        f"- SKU 行数：{len(data_rows)}",
        f"- Error：{errors}",
        "",
    ]
    if not findings:
        lines.extend([
            "未发现模板级问题。",
            "",
            "已确认：",
            "",
            "- Item Condition = New",
            "- Skip Offer 留空",
            "- List Price / Haul Price 已填写",
            "- 模板包含 Item Depth/Height/Width 字段时，其数值与单位成对填写",
            ""
        ])
    else:
        lines.extend(["## 问题清单", ""])
        for item in findings:
            lines.extend([
                f"### [ERROR] 行 {item['row']} - {item['field']}",
                "",
                f"- 问题：{item['message']}",
                f"- 建议：{item['fix']}",
                "",
            ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
