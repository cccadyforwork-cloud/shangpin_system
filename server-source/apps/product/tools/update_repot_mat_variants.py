from __future__ import annotations

from copy import copy
from pathlib import Path

from openpyxl import load_workbook


SOURCE = Path("/Users/cc/Desktop/1店8月w1上品/1店7月上品xin/换土垫/1店+换土垫.xlsx")
OUTPUT = Path("/Users/cc/Documents/GitHub/shangpin_system/outputs/换土垫多色多尺寸V1.xlsx")


FIELDS = {
    "sku": "contribution_sku#1.value",
    "product_type": "product_type#1.value",
    "record_action": "::record_action",
    "parentage": "parentage_level[marketplace_id=ATVPDKIKX0DER]#1.value",
    "parent_sku": "child_parent_sku_relationship[marketplace_id=ATVPDKIKX0DER]#1.parent_sku",
    "variation_theme": "variation_theme#1.name",
    "title": "item_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "brand": "brand[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "item_type_keyword": "item_type_keyword[marketplace_id=ATVPDKIKX0DER]#1.value",
    "model_number": "model_number[marketplace_id=ATVPDKIKX0DER]#1.value",
    "model_name": "model_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "manufacturer": "manufacturer[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "description": "product_description[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "bullet_1": "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "bullet_2": "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#2.value",
    "bullet_3": "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#3.value",
    "bullet_4": "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#4.value",
    "bullet_5": "bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#5.value",
    "generic_keyword": "generic_keyword[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "style": "style[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "material": "material[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "number_of_items": "number_of_items[marketplace_id=ATVPDKIKX0DER]#1.value",
    "item_package_quantity": "item_package_quantity[marketplace_id=ATVPDKIKX0DER]#1.value",
    "color": "color[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "size": "size[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "part_number": "part_number[marketplace_id=ATVPDKIKX0DER]#1.value",
    "shape": "item_shape[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "pattern": "pattern[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "unit_count": "unit_count[marketplace_id=ATVPDKIKX0DER]#1.value",
    "unit_count_type": "unit_count[marketplace_id=ATVPDKIKX0DER]#1.type[language_tag=en_US].value",
    "special_feature": "special_feature[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "mounting_type": "mounting_type[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
    "indoor": "indoor_outdoor_usage[marketplace_id=ATVPDKIKX0DER]#1.value",
    "outdoor": "indoor_outdoor_usage[marketplace_id=ATVPDKIKX0DER]#2.value",
    "item_depth": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.depth.value",
    "item_depth_unit": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.depth.unit",
    "item_height": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.height.value",
    "item_height_unit": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.height.unit",
    "item_width": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.width.value",
    "item_width_unit": "item_depth_width_height[marketplace_id=ATVPDKIKX0DER]#1.width.unit",
    "planter_form": "planter_form[marketplace_id=ATVPDKIKX0DER]#1.value",
    "has_drainage": "has_drainage[marketplace_id=ATVPDKIKX0DER]#1.value",
    "number_of_packs": "number_of_packs[marketplace_id=ATVPDKIKX0DER]#1.value",
    "condition": "condition_type[marketplace_id=ATVPDKIKX0DER]#1.value",
    "list_price": "list_price[marketplace_id=ATVPDKIKX0DER]#1.value",
    "haul_price": "purchasable_offer[marketplace_id=ATVPDKIKX0DER][audience=BZR]#1.our_price#1.schedule#1.value_with_tax",
    "package_length": "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.length.value",
    "package_length_unit": "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.length.unit",
    "package_width": "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.width.value",
    "package_width_unit": "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.width.unit",
    "package_height": "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.height.value",
    "package_height_unit": "item_package_dimensions[marketplace_id=ATVPDKIKX0DER]#1.height.unit",
    "package_weight": "item_package_weight[marketplace_id=ATVPDKIKX0DER]#1.value",
    "package_weight_unit": "item_package_weight[marketplace_id=ATVPDKIKX0DER]#1.unit",
    "display_weight": "item_display_weight[marketplace_id=ATVPDKIKX0DER]#1.value",
    "display_weight_unit": "item_display_weight[marketplace_id=ATVPDKIKX0DER]#1.unit",
    "country": "country_of_origin[marketplace_id=ATVPDKIKX0DER]#1.value",
    "batteries_required": "batteries_required[marketplace_id=ATVPDKIKX0DER]#1.value",
    "batteries_included": "batteries_included[marketplace_id=ATVPDKIKX0DER]#1.value",
    "dg": "supplier_declared_dg_hz_regulation[marketplace_id=ATVPDKIKX0DER]#1.value",
    "certificate": "required_product_compliance_certificate[marketplace_id=ATVPDKIKX0DER]#1.value",
}


VARIANTS = [
    {
        "sku": "TTCA-RepotMat-Green",
        "color": "Green",
        "size": "19.7 x 19.7 Inches",
        "cm": 50,
        "weight_g": 40,
        "price": 1.72,
    },
    {
        "sku": "TTCA-RepotMat-Green-66",
        "color": "Green",
        "size": "26 x 26 Inches",
        "cm": 66,
        "weight_g": 70,
        "price": 1.84,
    },
    {
        "sku": "TTCA-RepotMat-Yellow",
        "color": "Yellow",
        "size": "19.7 x 19.7 Inches",
        "cm": 50,
        "weight_g": 50,
        "price": 1.72,
    },
    {
        "sku": "TTCA-RepotMat-Yellow-66",
        "color": "Yellow",
        "size": "26 x 26 Inches",
        "cm": 66,
        "weight_g": 80,
        "price": 1.89,
    },
]


def inches(cm: float) -> float:
    return round(cm / 2.54, 2)


def pounds(grams: float) -> float:
    return round(grams / 453.59237, 2)


def title_for(variant: dict[str, object]) -> str:
    display_size = str(variant["size"]).replace(" x ", " X ")
    return (
        f"Repotting Mat for Indoor Gardening, {variant['color']} {display_size} "
        "Square Plant Transplanting Pad with Snap Corners"
    )


def description_for(variant: dict[str, object] | None = None) -> str:
    if variant is None:
        return (
            "Bring a cleaner setup to everyday plant care with this square repotting mat series. The mats open into practical work surfaces for small planters, succulents, herbs, seedlings, and routine soil changes on a table, floor, balcony, patio, or garden bench. Color and size options let shoppers choose the version that fits their usual potting space.\n\n"
            "The four snap corners connect to lift the edges into a shallow tray-like shape. This helps keep loose potting mix, trimmed leaves, and small tools closer to the work area while you fill pots, move seedlings, refresh soil, or organize small gardening supplies. When you want a flat surface again, the corners can be released for easier handling.\n\n"
            "After planting, open the corners and guide remaining soil back into a planter, bag, or cleanup container. The smooth coated surface is suited to quick wiping after normal use, so it works well for apartments, kitchens, patios, craft tables, and other spaces where a contained work area is helpful.\n\n"
            "This variation family includes green and yellow mats in about 19.7 by 19.7 inch and 26 by 26 inch options. Each version is lightweight, foldable, and easy to store between plant care sessions for repotting, soil mixing, pruning cleanup, seedling transfers, and organizing small planters without setting up a larger work station. The two color choices help separate different plant care tasks, while the two size choices support both quick countertop jobs and roomier floor or patio work. Keep one near regular planting supplies so the work area is ready when a plant needs attention."
        )
    color = str(variant["color"]).lower()
    compact = "compact" if variant["cm"] == 50 else "larger"
    return (
        f"Bring a cleaner setup to everyday plant care with this {color} square repotting mat. The mat opens into a {compact} work surface sized for planters, succulents, herbs, seedlings, and routine soil changes on a table, floor, balcony, patio, or garden bench. Its square format helps create a defined place for potting mix, trimming, and simple plant maintenance.\n\n"
        "The four snap corners connect to lift the edges into a shallow tray-like shape. This helps keep loose potting mix, trimmed leaves, and small tools closer to the work area while you fill pots, move seedlings, refresh soil, or organize small gardening supplies. When you want a flat surface again, the corners can be released for easier handling.\n\n"
        "After planting, open the corners and guide remaining soil back into a planter, bag, or cleanup container. The smooth coated surface is suited to quick wiping after normal use, so it works well for apartments, kitchens, patios, craft tables, and other spaces where a contained work area is helpful.\n\n"
        f"This listing is for one {color} mat in the {variant['size']} option. The lightweight foldable design stores easily between plant care sessions, making it a useful accessory for indoor and outdoor home gardening, soil mixing, pruning cleanup, seedling transfers, and organizing small planters without setting up a larger work station. The color and size are clearly assigned for the variation selector, so shoppers can choose the mat that matches their preferred setup before adding it to the cart. Keep it with regular planting supplies for quick access during routine plant care."
    )


def bullets_for(variant: dict[str, object] | None = None) -> list[str]:
    if variant is None:
        return [
            "Contained Potting Area: Raised snap corners help shape the square mat into a shallow work area for soil mixing, seedling transfers, succulent care, and planting jobs on a table, floor, balcony, patio, or garden bench.",
            "Two Size Options: Choose about 19.7 by 19.7 inches for compact tabletop work or about 26 by 26 inches when a larger square surface is helpful for bigger planters, extra potting mix, and small tool placement.",
            "Easy Cleanup Surface: Smooth coated material helps guide loose soil, leaves, and potting mix back into a container or planter after use, making routine repotting simpler for apartments, kitchens, patios, and work tables.",
            "Snap Corner Design: Four corner fasteners lift the edges when connected, helping reduce soil scatter during watering, filling, pruning, and transplanting tasks while keeping the mat simple to open flat again.",
            "Color Choices Available: Includes green and yellow options in a lightweight foldable format for succulents, herbs, seedlings, and tabletop planters, with each mat easy to move, open, clean, refold, and store after use.",
        ]
    color = str(variant["color"]).lower()
    size = str(variant["size"])
    return [
        "Contained Potting Area: Raised snap corners help shape the square mat into a shallow work area for soil mixing, seedling transfers, succulent care, and planting jobs on a table, floor, balcony, patio, or garden bench.",
        f"Clear Size Selection: The opened work surface measures about {size.lower()}, giving shoppers a direct size choice for tabletop, floor, balcony, or patio work while still folding down neatly for storage.",
        "Easy Cleanup Surface: Smooth coated material helps guide loose soil, leaves, and potting mix back into a container or planter after use, making routine repotting simpler for apartments, kitchens, patios, and work tables.",
        "Snap Corner Design: Four corner fasteners lift the edges when connected, helping reduce soil scatter during watering, filling, pruning, and transplanting tasks while keeping the mat simple to open flat again.",
        f"Single {variant['color']} Mat: Includes one {color} repotting work mat for succulents, herbs, seedlings, and tabletop planters, with a lightweight build that is easy to move, open, clean, refold, and store after use.",
    ]


def set_value(ws, row: int, cols: dict[str, int], key: str, value) -> None:
    col = cols.get(FIELDS[key])
    if col:
        ws.cell(row, col).value = value


def copy_row(ws, source_row: int, target_row: int) -> None:
    ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height
    for col in range(1, ws.max_column + 1):
        src = ws.cell(source_row, col)
        dst = ws.cell(target_row, col)
        dst.value = src.value
        if src.has_style:
            dst._style = copy(src._style)
        if src.number_format:
            dst.number_format = src.number_format
        if src.alignment:
            dst.alignment = copy(src.alignment)
        if src.protection:
            dst.protection = copy(src.protection)
        if src.comment:
            dst.comment = copy(src.comment)


def apply_parent(ws, cols: dict[str, int]) -> None:
    row = 7
    set_value(ws, row, cols, "title", "Repotting Mat for Indoor Gardening, Square Plant Transplanting Pad, Multiple Colors Available, Multiple Styles Available")
    set_value(ws, row, cols, "description", description_for())
    for idx, bullet in enumerate(bullets_for(), start=1):
        set_value(ws, row, cols, f"bullet_{idx}", bullet)


def apply_child(ws, cols: dict[str, int], row: int, variant: dict[str, object]) -> None:
    for key, value in {
        "sku": variant["sku"],
        "product_type": "PLANTER",
        "record_action": "Create or Replace (Full Update)",
        "parentage": "Child",
        "parent_sku": "TTCA-RepotMat-R",
        "variation_theme": "COLOR/SIZE",
        "title": title_for(variant),
        "brand": "Generic",
        "item_type_keyword": "garden-pots",
        "model_number": variant["sku"],
        "model_name": "Repotting Mat",
        "manufacturer": "Generic",
        "description": description_for(variant),
        "generic_keyword": "repotting mat, potting mat, plant transplanting pad, gardening work mat, soil mat, succulent planting mat, balcony gardening mat",
        "style": "Garden",
        "material": "Polyethylene (PE)",
        "number_of_items": 1,
        "item_package_quantity": 1,
        "color": variant["color"],
        "size": variant["size"],
        "part_number": variant["sku"],
        "shape": "Square",
        "pattern": "Solid",
        "unit_count": 1,
        "unit_count_type": "Count",
        "special_feature": "Foldable",
        "mounting_type": "Tabletop",
        "indoor": "Indoor",
        "outdoor": "Outdoor",
        "item_depth": inches(float(variant["cm"])),
        "item_depth_unit": "Inches",
        "item_height": 0.2,
        "item_height_unit": "Inches",
        "item_width": inches(float(variant["cm"])),
        "item_width_unit": "Inches",
        "planter_form": "Tray",
        "has_drainage": "No",
        "number_of_packs": 1,
        "condition": "New",
        "list_price": variant["price"],
        "haul_price": variant["price"],
        "package_length": inches(float(variant["cm"]) / 2),
        "package_length_unit": "Inches",
        "package_width": inches(float(variant["cm"]) / 2),
        "package_width_unit": "Inches",
        "package_height": 0.79,
        "package_height_unit": "Inches",
        "package_weight": pounds(float(variant["weight_g"])),
        "package_weight_unit": "Pounds",
        "display_weight": pounds(float(variant["weight_g"])),
        "display_weight_unit": "Pounds",
        "country": "China",
        "batteries_required": "No",
        "batteries_included": "No",
        "dg": "Not Applicable",
        "certificate": "Not Applicable",
    }.items():
        set_value(ws, row, cols, key, value)
    for idx, bullet in enumerate(bullets_for(variant), start=1):
        set_value(ws, row, cols, f"bullet_{idx}", bullet)


def main() -> None:
    wb = load_workbook(SOURCE)
    ws = wb["Template"]
    cols = {
        str(ws.cell(5, col).value).strip(): col
        for col in range(1, ws.max_column + 1)
        if ws.cell(5, col).value
    }

    apply_parent(ws, cols)
    for offset, variant in enumerate(VARIANTS):
        row = 8 + offset
        if row != 8:
            copy_row(ws, 8, row)
        apply_child(ws, cols, row, variant)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
