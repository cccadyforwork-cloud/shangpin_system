"""Default-workbench package values derived from its shipping-fee tier."""

import json
from decimal import Decimal, InvalidOperation

from .paths import CONFIG_DIR


PACKAGE_FIELDS = (
    "package_length_in",
    "package_width_in",
    "package_height_in",
    "package_weight_lb",
)


def workbench_logistics_options():
    path = CONFIG_DIR / "logistics_tiers.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    tiers = {str(item.get("id")): item for item in data.get("tiers", [])}
    options = []
    for item in data.get("workbench_fee_options", [])[:4]:
        tier = tiers.get(str(item.get("tier_id"))) or {}
        package_cm = tier.get("package_cm") or []
        options.append({
            "id": str(item.get("id") or ""),
            "label": str(item.get("label") or ""),
            "fee": item.get("fee_usd"),
            "packageLengthIn": round(float(package_cm[0]) / 2.54, 2) if len(package_cm) > 0 else "",
            "packageWidthIn": round(float(package_cm[1]) / 2.54, 2) if len(package_cm) > 1 else "",
            "packageHeightIn": round(float(package_cm[2]) / 2.54, 2) if len(package_cm) > 2 else "",
            "packageWeightLb": round(float(tier.get("default_weight_grams")) / 453.592, 2) if tier.get("default_weight_grams") else "",
        })
    return options


def _same_fee(left, right):
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, TypeError, ValueError):
        return False


def apply_workbench_package_defaults(rows):
    """Overwrite package fields for priced rows with the selected tier defaults.

    A fee can identify a tier when a source sheet has no explicit tier ID. Parent
    rows carry no offer or package dimensions. Returns whether any row changed.
    """
    options = workbench_logistics_options()
    by_id = {item["id"]: item for item in options}
    changed = False
    for row in rows:
        if str(row.get("parentage_level") or "").strip().lower() == "parent":
            for field in (*PACKAGE_FIELDS, "logistics_tier", "shipping_fee_usd"):
                if row.get(field) not in (None, ""):
                    row[field] = ""
                    changed = True
            continue
        selected = by_id.get(str(row.get("logistics_tier") or "").strip())
        if selected is None and row.get("shipping_fee_usd") not in (None, ""):
            selected = next((item for item in options if _same_fee(item["fee"], row["shipping_fee_usd"])), None)
        if selected is None:
            continue
        defaults = {
            "logistics_tier": selected["id"],
            "shipping_fee_usd": str(selected["fee"]),
            "package_length_in": str(selected["packageLengthIn"]),
            "package_width_in": str(selected["packageWidthIn"]),
            "package_height_in": str(selected["packageHeightIn"]),
            "package_weight_lb": str(selected["packageWeightLb"]),
        }
        for field, value in defaults.items():
            if str(row.get(field) or "") != value:
                row[field] = value
                changed = True
    return changed
