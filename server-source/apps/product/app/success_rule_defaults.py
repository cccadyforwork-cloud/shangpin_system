import json
from functools import lru_cache
from pathlib import Path

from .paths import DATA_DIR


RULES_JSON = DATA_DIR / "success_template_rules.json"

SAFE_FIELD_SUFFIXES = (
    ".unit",
    "#1.unit",
    "#1.value",
    "#1.type[language_tag=en_US]#1.value",
    "#1.type[language_tag=en_US].value",
    "#1.size_system",
    "#1.width",
    "#1.age_group",
    "#1.gender",
    "#1.value",
)

SAFE_VALUE_ALLOWLIST = {
    "Adult",
    "Buckle",
    "China",
    "CN",
    "Count",
    "Cotton",
    "Generic",
    "Imported",
    "Inches",
    "Machine Wash",
    "Medium",
    "New",
    "No",
    "Not Applicable",
    "Pounds",
    "Regular",
    "Unisex",
    "US Footwear Size System",
    "Women",
}

UNSAFE_FIELD_KEYWORDS = (
    "audience",
    "bullet_point",
    "color",
    "contribution_sku",
    "description",
    "depth.value",
    "display_dimensions",
    "display_weight",
    "height.value",
    "image",
    "item_name",
    "length.value",
    "list_price",
    "main_product",
    "maximum_seller_allowed_price",
    "media_location",
    "minimum_seller_allowed_price",
    "model_number",
    "our_price",
    "package_dimensions",
    "package_weight",
    "part_number",
    "product_description",
    "purchasable_offer",
    "size[",
    "skip_offer",
    "standardized_values",
    "swatch",
    "unit_count[marketplace_id=ATVPDKIKX0DER]#1.value",
    "width.value",
)

UNSAFE_EXACT_FIELDS = {
    "::record_action",
    "item_type_keyword[marketplace_id=ATVPDKIKX0DER]#1.value",
    "parentage_level[marketplace_id=ATVPDKIKX0DER]#1.value",
    "product_type#1.value",
    "variation_theme#1.name",
}


def load_safe_defaults(product_type, rules_path=None, existing_fields=None):
    rules_path = Path(rules_path) if rules_path else RULES_JSON
    if not product_type or not rules_path.exists():
        return {}

    rules = _load_rules(str(rules_path))
    product_rules = rules.get("product_types", {}).get(str(product_type))
    if not product_rules:
        return {}

    existing_fields = set(existing_fields or [])
    defaults = {}
    for item in product_rules.get("fixed_default_fields", []):
        field_name = item.get("field_name", "")
        value = item.get("value", "")
        if item.get("mapped_by_auto_fill"):
            continue
        if field_name in existing_fields:
            continue
        if _is_safe_default(field_name, value):
            defaults[field_name] = value
    return defaults


@lru_cache(maxsize=8)
def _load_rules(rules_path):
    return json.loads(Path(rules_path).read_text(encoding="utf-8"))


def _is_safe_default(field_name, value):
    if not field_name or value in (None, ""):
        return False
    if field_name in UNSAFE_EXACT_FIELDS:
        return False
    lowered = field_name.lower()
    if any(keyword in lowered for keyword in UNSAFE_FIELD_KEYWORDS):
        return False
    if value not in SAFE_VALUE_ALLOWLIST:
        return False
    return field_name.endswith(SAFE_FIELD_SUFFIXES)
