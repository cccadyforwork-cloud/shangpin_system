import re
import unicodedata
from html import unescape
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

from .paths import OUTPUTS_DIR, safe_name
from .workbook_io import write_intake_workbook


SUPPORTED_TEXT_EXT = {".txt", ".md", ".csv", ".tsv", ".html", ".htm"}
SUPPORTED_EXCEL_EXT = {".xlsx", ".xlsm"}
SUPPORTED_PDF_EXT = {".pdf"}
URL_RE = re.compile(r"https?://[^\s,，;；)）]+", re.I)
PRICE_RE = re.compile(r"(?:¥|￥|\$|usd|rmb|价格|售价|成本|单价)[:：\s]*([0-9]+(?:\.[0-9]+)?)", re.I)
UNIT_PRICE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*元\s*/\s*个", re.I)
WEIGHT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(kg|kgs|g|gram|grams|lb|lbs|pound|pounds)\b", re.I)
SIZE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*[xX*×]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:[xX*×]\s*([0-9]+(?:\.[0-9]+)?))?\s*(cm|mm|in|inch|inches)?", re.I)
SKU_RE = re.compile(r"\b[A-Z0-9][A-Z0-9_-]{4,}\b")
ORDER_ITEM_CODE_RE = re.compile(r"(?m)^\s*\d+\s+([A-Z0-9-]{3,})\s*$")
CHINESE_COLOR_RE = re.compile(
    r"(?:颜色|顏色)\s*[:：]\s*(?:[0-9]+(?:\.[0-9]+)?\s*g\s*)?(?:瑜\s*伽\s*砖\s*)?-\s*([^\s,，;；]+)"
)


COLOR_WORDS = {
    "black": "Black",
    "white": "White",
    "red": "Red",
    "blue": "Blue",
    "green": "Green",
    "pink": "Pink",
    "gray": "Gray",
    "grey": "Gray",
    "yellow": "Yellow",
    "purple": "Purple",
    "orange": "Orange",
    "transparent": "Transparent",
    "黑": "Black",
    "黑色": "Black",
    "白": "White",
    "白色": "White",
    "红": "Red",
    "红色": "Red",
    "蓝": "Blue",
    "蓝色": "Blue",
    "绿": "Green",
    "绿色": "Green",
    "粉": "Pink",
    "粉色": "Pink",
    "灰": "Gray",
    "灰色": "Gray",
    "黄": "Yellow",
    "黄色": "Yellow",
    "紫": "Purple",
    "紫色": "Purple",
    "橙": "Orange",
    "橙色": "Orange",
    "透明": "Transparent",
    "透明色": "Transparent"
}


MATERIAL_WORDS = {
    "metal": "Metal",
    "silicone": "Silicone",
    "plastic": "Plastic",
    "stainless steel": "Stainless Steel",
    "wood": "Wood",
    "cotton": "Cotton",
    "polyester": "Polyester",
    "nylon": "Nylon",
    "abs": "ABS",
    "硅胶": "Silicone",
    "塑料": "Plastic",
    "不锈钢": "Stainless Steel",
    "木": "Wood",
    "棉": "Cotton",
    "涤纶": "Polyester",
    "尼龙": "Nylon"
}


RISK_WORDS = [
    "food",
    "食品",
    "skin",
    "皮肤",
    "medical",
    "medicine",
    "医疗",
    "治疗",
    "cure",
    "treat",
    "pain relief",
    "brand",
    "logo",
    "trademark",
    "品牌",
    "商标"
]


SOURCE_FOLDERS = {
    "01_采购资料",
    "03_竞品参考",
    "07_上架备注"
}

TEMPLATE_FOLDERS = {
    "04_模板原件",
    "05_填表版本"
}


def _read_text_file(path):
    return Path(path).read_text(encoding="utf-8-sig", errors="ignore")


def _read_excel_file(path):
    chunks = []
    wb = load_workbook(path, data_only=True, read_only=True)
    for ws in wb.worksheets:
        chunks.append(f"Sheet: {ws.title}")
        for row in ws.iter_rows(values_only=True):
            values = [str(value).strip() for value in row if value not in (None, "")]
            if values:
                chunks.append(" | ".join(values))
    return "\n".join(chunks)


def _read_pdf_file(path):
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return unicodedata.normalize("NFKC", "\n".join(chunks))


def _read_html_file(path):
    text = _read_text_file(path)
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(div|p|li|tr|h[1-6])>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    if title_match:
        title = unescape(re.sub(r"\s+", " ", title_match.group(1))).strip()
        text = f"HTML_TITLE: {title}\n{text}"
    return re.sub(r"[ \t]+", " ", text)


def _collect_sources(project_dir):
    project_dir = Path(project_dir)
    sources = []
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("~$") or path.name == ".DS_Store":
            continue
        if path.parent.name not in SOURCE_FOLDERS:
            continue
        if path.suffix.lower() in SUPPORTED_EXCEL_EXT and (
            "产品资料" in path.name or "自动提炼草稿" in path.name
        ):
            continue
        if "自动提炼草稿" in path.name or "资料提炼报告" in path.name:
            continue
        suffix = path.suffix.lower()
        try:
            if suffix in {".html", ".htm"}:
                text = _read_html_file(path)
            elif suffix in SUPPORTED_TEXT_EXT:
                text = _read_text_file(path)
            elif suffix in SUPPORTED_EXCEL_EXT:
                text = _read_excel_file(path)
            elif suffix in SUPPORTED_PDF_EXT:
                text = _read_pdf_file(path)
            else:
                continue
        except Exception as exc:
            sources.append((path, f"[读取失败: {exc}]"))
            continue
        sources.append((path, text))
    return sources


def _first_match(pattern, text, group=1):
    match = pattern.search(text)
    if not match:
        return ""
    if match.lastindex:
        return match.group(group).strip()
    return match.group(0).strip()


def _extract_named_value(labels, text):
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\s*[:：]\s*([^\n\r|,，;；]+)", re.I)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ""


def _convert_size_to_inches(match):
    values = [float(match.group(i)) for i in [1, 2, 3] if match.group(i)]
    unit = (match.group(4) or "").lower()
    if unit in {"cm", ""}:
        values = [round(value / 2.54, 2) for value in values]
    elif unit == "mm":
        values = [round(value / 25.4, 2) for value in values]
    else:
        values = [round(value, 2) for value in values]
    while len(values) < 3:
        values.append("")
    return values[:3]


def _convert_weight_to_lb(match):
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit in {"kg", "kgs"}:
        return round(value * 2.20462, 2)
    if unit in {"g", "gram", "grams"}:
        return round(value / 453.59237, 2)
    return round(value, 2)


def _guess_from_words(words, text):
    lowered = text.lower()
    for key, value in words.items():
        if key.lower() in lowered:
            return value
    return ""


def _guess_product_name(project_dir, text):
    project_name = Path(project_dir).name.split("_", 1)[-1]
    if "瑜伽砖" in project_name:
        return "Yoga Block"
    if "花束卡片夹" in project_name:
        return "Floral Card Holder Picks"
    if project_name and not project_name.startswith("20"):
        return project_name

    named = _extract_named_value(["产品名", "品名", "商品名称", "product name", "item name", "title"], text)
    if named and "amazon haul" not in named.lower():
        return named[:120]

    lines = [line.strip(" -\t") for line in text.splitlines() if len(line.strip()) >= 4]
    for line in lines[:20]:
        if not URL_RE.search(line) and not PRICE_RE.search(line):
            return line[:120]
    return Path(project_dir).name.split("_", 1)[-1]


def _guess_category(text):
    lowered = text.lower()
    if any(word in lowered for word in ["floral", "bouquet", "flower", "card holder", "花束", "鲜花", "卡片夹", "卡插"]):
        return "home"
    if any(word in lowered for word in ["yoga", "pilates", "fitness", "exercise", "瑜伽", "健身", "运动"]):
        return "sports"
    if any(word in lowered for word in ["kitchen", "厨房", "cookware", "utensil"]):
        return "kitchen"
    if any(word in lowered for word in ["toy", "玩具"]):
        return "toy"
    if any(word in lowered for word in ["pet", "宠物"]):
        return "pet"
    if any(word in lowered for word in ["beauty", "makeup", "cosmetic", "美妆"]):
        return "beauty"
    if any(word in lowered for word in ["home", "storage", "收纳", "家居"]):
        return "home"
    return ""


def _guess_route(text, price, brand_hint=""):
    if brand_hint and brand_hint.lower() != "generic":
        return "Brand"
    if price and price <= 20:
        return "Haul Generic"
    return "Haul Generic"


def _make_sku(product_name):
    words = re.findall(r"[A-Za-z0-9]+", product_name.upper())
    base = "-".join(words[:4]) if words else safe_name(product_name).upper()
    return f"{base[:32]}-001"


def _sku_base(product_name):
    words = re.findall(r"[A-Za-z0-9]+", product_name.upper())
    if words:
        return "-".join(words[:4])[:24]
    if "瑜伽" in product_name:
        return "YOGA-BLOCK"
    return "PRODUCT"


def _single_link_sku(product_name):
    return f"{_sku_base(product_name)}-001"


def _sku_for_color(product_name, color, index):
    if "yoga" in product_name.lower() or "瑜伽" in product_name:
        return f"YOGA-Block-{color}"
    base = _sku_base(product_name)
    color_part = re.sub(r"[^A-Z0-9]+", "", str(color).upper()) or f"{index:02d}"
    return f"{base}-{color_part}-{index:02d}"


def _make_copy(product_name, color, size, material, set_count):
    subject = product_name or "Product"
    set_text = f", {set_count} Pack" if set_count else ""
    tail = ", ".join(value for value in [color, size] if value)
    title = f"{subject}{set_text}" + (f", {tail}" if tail else "")
    is_yoga = "yoga" in subject.lower() or "瑜伽" in subject
    is_floral_card_holder = "floral card holder" in subject.lower() or "花束卡片夹" in subject
    if is_floral_card_holder:
        title = f"Floral Card Holder Picks, {color}, Metal Flower Bouquet Card Sticks for Gift Cards and Table Centerpieces"
        bullet_1 = "Designed for flower bouquets, gift cards, table centerpieces, party signs, and photo notes."
        bullet_2 = f"Made with {material or 'metal'} for a clean decorative look in floral arrangements."
        bullet_3 = "Slim pick design slides into bouquets, foam, vases, baskets, and display arrangements."
        bullet_4 = "Useful for weddings, birthdays, flower shops, gift wrapping, and event table decor."
        bullet_5 = "Lightweight pieces are easy to place, remove, store, and reuse for seasonal displays."
        desc = "These floral card holder picks help display cards, photos, notes, and small signs in bouquets, centerpieces, baskets, and party arrangements. The slim metal design is suitable for flower shops, weddings, birthdays, gift displays, and home decoration."
    elif is_yoga:
        bullet_1 = "Supports yoga poses, balance practice, stretching routines, and studio sessions."
        bullet_2 = f"Made with lightweight {material} for steady everyday practice." if material else "Made with lightweight foam for steady everyday practice."
        bullet_3 = "Beveled edges provide a comfortable grip during floor and standing poses."
        bullet_4 = f"Includes {set_count} piece set for home, gym, or studio use." if set_count else "Works well for home, gym, or studio use."
        bullet_5 = "Compact shape is easy to carry, stack, and store between sessions."
        desc = f"{subject} helps add lift, reach, and stability during yoga, stretching, and balance practice. The lightweight block is easy to carry and store for home, gym, and studio routines."
    else:
        bullet_1 = "Designed for everyday use in practical home, travel, or work settings."
        bullet_2 = f"Made with {material} for simple daily handling." if material else "Made for simple daily handling and repeated use."
        bullet_3 = "Compact design helps keep items organized without taking up extra space."
        bullet_4 = f"Includes {set_count} piece set for convenient replacement or sharing." if set_count else "Includes the product shown in the listing photos."
        bullet_5 = "Easy to carry, store, and use for a wide range of everyday needs."
        desc = f"{subject} is designed for everyday use with a simple, practical structure. It works well for home, travel, office, and general organization needs."
    return title, [bullet_1, bullet_2, bullet_3, bullet_4, bullet_5], desc


def _extract_color_variants(text):
    searchable = re.sub(r"\s+", " ", text)
    colors = []
    for color in CHINESE_COLOR_RE.findall(searchable):
        normalized = COLOR_WORDS.get(color, COLOR_WORDS.get(color.replace("色", ""), color))
        if normalized not in colors:
            colors.append(normalized)
    return colors


def _extract_floral_card_holder_variants(text):
    normalized_text = text.replace("⻆", "角")
    searchable = re.sub(r"\s+", "", normalized_text)
    variant_map = {
        "圆形卡插": ("Round", 1.5),
        "五角星卡插": ("Star", 1.5),
        "镀金小熊": ("Gold Bear", 3.0),
        "心形卡插": ("Heart", 1.5),
        "圆形粉色": ("Pink Round", 3.0),
    }
    variants = []
    for chinese_name, (english_name, fallback_price) in variant_map.items():
        if chinese_name in searchable:
            variants.append({
                "name": english_name,
                "cost": fallback_price,
            })
    return variants


def _guess_cost(text):
    unit_price = _first_match(UNIT_PRICE_RE, text)
    if unit_price:
        return float(unit_price)
    price = _first_match(PRICE_RE, text)
    return float(price) if price else ""


def _guess_main_image_url(urls):
    return ""


def _guess_item_type_keyword(project_dir, product_name, text):
    template_keyword = _extract_browse_node_from_templates(project_dir)
    if template_keyword:
        return template_keyword

    lowered = f"{product_name}\n{text}".lower()
    if "floral" in lowered or "bouquet" in lowered or "flower" in lowered or "花束" in lowered or "卡插" in lowered:
        return template_keyword or "cookbook-stands"
    if "yoga" in lowered or "瑜伽砖" in lowered:
        return "yoga-blocks"
    if "storage" in lowered or "收纳" in lowered:
        return "storage-bags"
    return "-".join(re.findall(r"[a-z0-9]+", product_name.lower())[:4])


def _extract_browse_node_from_templates(project_dir):
    project_dir = Path(project_dir)
    for folder in TEMPLATE_FOLDERS:
        template_dir = project_dir / folder
        if not template_dir.exists():
            continue
        for path in template_dir.glob("*"):
            if path.suffix.lower() not in SUPPORTED_EXCEL_EXT or path.name.startswith("~$"):
                continue
            try:
                wb = load_workbook(path, data_only=True, read_only=True, keep_vba=path.suffix.lower() == ".xlsm")
            except Exception:
                continue
            if "Browse Data" not in wb.sheetnames:
                continue
            ws = wb["Browse Data"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                value = row[0] if row and row[0] else None
                if value:
                    return str(value).strip()
    return ""


def _extract_product_type_from_templates(project_dir):
    project_dir = Path(project_dir)
    for folder in TEMPLATE_FOLDERS:
        template_dir = project_dir / folder
        if not template_dir.exists():
            continue
        for path in template_dir.glob("*"):
            if path.suffix.lower() not in SUPPORTED_EXCEL_EXT or path.name.startswith("~$"):
                continue
            if "EXERCISE_BLOCK" in path.stem.upper():
                return "EXERCISE_BLOCK"
            try:
                wb = load_workbook(path, data_only=True, read_only=True, keep_vba=path.suffix.lower() == ".xlsm")
            except Exception:
                continue
            if "Valid Values" not in wb.sheetnames:
                continue
            ws = wb["Valid Values"]
            for row in ws.iter_rows(values_only=True):
                values = [str(value).strip() if value is not None else "" for value in row]
                for idx, value in enumerate(values):
                    if value.startswith("Product Type"):
                        product_type = next((item for item in values[idx + 1:] if item), "")
                        if product_type:
                            return product_type
    return ""


def analyze_project(project_dir, output_path=None):
    project_dir = Path(project_dir)
    sources = _collect_sources(project_dir)
    combined = "\n".join(text for _path, text in sources)

    urls = URL_RE.findall(combined)
    target_price = _guess_cost(combined)

    size_match = SIZE_RE.search(combined)
    length, width, height = _convert_size_to_inches(size_match) if size_match else ("", "", "")

    weight_match = WEIGHT_RE.search(combined)
    weight = _convert_weight_to_lb(weight_match) if weight_match else ""

    product_name = _guess_product_name(project_dir, combined)
    variant_colors = _extract_color_variants(combined)
    floral_variants = _extract_floral_card_holder_variants(combined)
    color = variant_colors[0] if variant_colors else (_extract_named_value(["颜色", "color"], combined) or _guess_from_words(COLOR_WORDS, combined))
    size = _extract_named_value(["尺寸", "规格", "size"], combined)
    material = _extract_named_value(["材质", "material"], combined) or _guess_from_words(MATERIAL_WORDS, combined)
    set_count = _extract_named_value(["套装数", "数量", "pack", "set count"], combined)
    brand_hint = _extract_named_value(["品牌", "brand"], combined)
    category = _guess_category(combined)
    product_type = _extract_product_type_from_templates(project_dir)
    route = _guess_route(combined, target_price if isinstance(target_price, float) else None, brand_hint)
    brand = brand_hint if route == "Brand" and brand_hint else "Generic"
    manufacturer = brand
    base_sku = _extract_named_value(["SKU", "sku", "货号"], combined)
    supplier_link = next((url for url in urls if "1688.com" in url or "alibaba" in url), urls[0] if urls else "")
    competitor_links = "\n".join(url for url in urls if "amazon." in url)
    main_image_url = _guess_main_image_url(urls)
    item_type_keyword = _guess_item_type_keyword(project_dir, product_name, combined)
    source_colors = ", ".join(variant_colors) if variant_colors else color
    if floral_variants:
        colors_for_rows = [item["name"] for item in floral_variants]
    else:
        colors_for_rows = variant_colors or ([color] if color else [""])

    rows = []
    for index, row_color in enumerate(colors_for_rows, 1):
        floral_variant = floral_variants[index - 1] if floral_variants else None
        if floral_variant:
            row_sku = f"FLORAL-CARD-HOLDER-{re.sub(r'[^A-Z0-9]+', '-', row_color.upper()).strip('-')}"
        elif len(colors_for_rows) > 1:
            row_sku = f"{base_sku}-{row_color}" if base_sku else _sku_for_color(product_name, row_color, index)
        else:
            row_sku = base_sku or _single_link_sku(product_name)
        title, bullets, description = _make_copy(product_name, row_color, size, material, set_count)
        rows.append({
            "project_name": project_dir.name,
            "product_name": product_name,
            "route": route,
            "brand": brand,
            "manufacturer": manufacturer,
            "category": category,
            "product_type": product_type,
            "item_type_keyword": item_type_keyword,
            "sku": row_sku,
            "color": row_color,
            "size": size,
            "set_count": set_count or (10 if floral_variant else ""),
            "material": material,
            "accessories": _extract_named_value(["配件", "accessories"], combined),
            "cost": floral_variant["cost"] if floral_variant else target_price,
            "target_price": "",
            "list_price": "",
            "haul_price": "",
            "package_length_in": length,
            "package_width_in": width,
            "package_height_in": height,
            "package_weight_lb": weight,
            "country_of_origin": "China",
            "batteries_required": "No",
            "dangerous_goods": "No",
            "main_image_url": main_image_url,
            "supplier_link": supplier_link,
            "competitor_links": competitor_links,
            "title": title,
            "bullet_1": bullets[0],
            "bullet_2": bullets[1],
            "bullet_3": bullets[2],
            "bullet_4": bullets[3],
            "bullet_5": bullets[4],
            "description": description,
            "notes": f"独立链接路线：每个款式单独 SKU，不设置 Parent/Child 变体。采购单款式：{source_colors}。List Price 留空人工填写；Haul Price 后续与 List Price 保持一致。"
        })

    if output_path is None:
        output_path = project_dir / "07_上架备注" / f"{safe_name(project_dir.name)}_自动提炼草稿.xlsx"
    write_intake_workbook(output_path, rows)

    report_path = OUTPUTS_DIR / f"{safe_name(project_dir.name)}_资料提炼报告.md"
    _write_analysis_report(report_path, project_dir, sources, rows, combined)
    return output_path, report_path


def _write_analysis_report(path, project_dir, sources, rows, combined):
    row = rows[0] if rows else {}
    risk_text = "\n".join(text for source_path, text in sources if source_path.suffix.lower() not in {".html", ".htm"})
    risk_hits = [word for word in RISK_WORDS if word.lower() in risk_text.lower()]
    source_lines = [f"- {source_path}" for source_path, _text in sources]
    lines = [
        f"# {Path(project_dir).name} 资料提炼报告",
        "",
        "## 已读取资料",
        "",
        *(source_lines or ["- 未找到可读取的 txt/md/csv/tsv/xlsx/xlsm/pdf/html 资料。"]),
        "",
        "## 提炼结果",
        "",
        f"- 产品名：{row.get('product_name')}",
        f"- 路线建议：{row.get('route')}",
        f"- Brand：{row.get('brand')}",
        f"- 类目猜测：{row.get('category')}",
        f"- SKU：{row.get('sku')}",
        f"- 颜色：{', '.join(str(item.get('color')) for item in rows if item.get('color'))}",
        f"- 草稿 SKU 数：{len(rows)}",
        f"- 尺寸 inch：{row.get('package_length_in')} x {row.get('package_width_in')} x {row.get('package_height_in')}",
        f"- 重量 lb：{row.get('package_weight_lb')}",
        f"- 链接数量：{len(URL_RE.findall(combined))}",
        "",
        "## 需要人工确认",
        "",
        "- item_type_keyword",
        "- List Price / Haul Price",
        "- 主图 URL 是否是可公开访问的图片直链",
        "- 是否真的适合 Generic 或 Haul Generic",
        "- 亚马逊模板里的条件必填字段",
        ""
    ]
    if risk_hits:
        lines.extend([
            "## 风险词命中",
            "",
            ", ".join(sorted(set(risk_hits))),
            ""
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
