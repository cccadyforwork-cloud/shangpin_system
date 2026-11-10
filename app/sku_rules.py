"""Shared SKU naming rules for every new-listing route."""

import re


SKU_UNIT_TOKENS = {
    "pc", "pcs", "set", "sets",
    "mm", "cm", "m",
    "in", "inch", "inches",
    "oz", "lb", "lbs",
    "g", "kg",
    "ml", "l",
}


def store_sku_prefix(store_id):
    """Store 1 uses TTCA; every other target store uses CA."""
    return "TTCA" if str(store_id or "").strip() == "1店" else "CA"


def sku_title_word(word, *, lowercase_units=False):
    text = str(word or "")
    if text.isdigit():
        return text
    if lowercase_units and text.lower() in SKU_UNIT_TOKENS:
        return text.lower()
    return text[:1].upper() + text[1:].lower()


def product_sku_token(value):
    """Use at most two meaningful English/alphanumeric words, joined directly."""
    words = re.findall(r"[A-Za-z0-9]+", str(value or ""))[:2]
    token = "".join(sku_title_word(word) for word in words)
    return token[:20] or "Product"


def attribute_sku_token(value):
    words = re.findall(r"[A-Za-z0-9]+", str(value or ""))
    return "".join(sku_title_word(word, lowercase_units=True) for word in words)


def quantity_sku_token(value):
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    if not match:
        return ""
    number = match.group(0)
    if number.endswith(".0"):
        number = number[:-2]
    return f"{number}P"


def generated_parent_sku(product_name, store_id=""):
    return f"{store_sku_prefix(store_id)}-{product_sku_token(product_name)}"


def variant_sku_suffix(*, variation_theme="", color="", size="", set_count="", set_name="", index=1):
    """Build the child suffix from the actual variation dimensions."""
    theme = str(variation_theme or "").upper()
    tokens = []
    if "COLOR" in theme:
        token = attribute_sku_token(color)
        if token:
            tokens.append(token)
    if "SIZE" in theme:
        token = attribute_sku_token(size)
        if token:
            tokens.append(token)
    if "NUMBER_OF_ITEMS" in theme or "ITEM_PACKAGE_QUANTITY" in theme:
        token = quantity_sku_token(set_count)
        if token:
            tokens.append(token)
    if "SET_NAME" in theme:
        token = attribute_sku_token(set_name or size or color)
        if token and token not in tokens:
            tokens.append(token)
    if not tokens:
        for value in (color, size):
            token = attribute_sku_token(value)
            if token and token not in tokens:
                tokens.append(token)
        quantity = quantity_sku_token(set_count)
        if quantity:
            tokens.append(quantity)
    return "-".join(tokens) or f"Option{int(index):03d}"


def generated_child_sku(parent_sku, *, variation_theme="", color="", size="", set_count="", set_name="", index=1):
    suffix = variant_sku_suffix(
        variation_theme=variation_theme,
        color=color,
        size=size,
        set_count=set_count,
        set_name=set_name,
        index=index,
    )
    return f"{parent_sku}-{suffix}"
