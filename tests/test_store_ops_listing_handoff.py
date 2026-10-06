from app.analyzer import make_copy_for_row
from app.listing_rules import validate_listing_row
from app.validator import validate_intake
from app.variation_title_rules import apply_variation_title_rules
from app.workbook_io import write_intake_workbook


def test_parent_manufacturer_can_be_blank_in_intake(tmp_path):
    path = tmp_path / "intake.xlsx"
    write_intake_workbook(path, [{
        "project_name": "beads",
        "product_name": "AB Beads",
        "route": "Haul Generic Variation",
        "brand": "Generic",
        "manufacturer": "",
        "sku": "TTCA-DiscBeads",
        "parentage_level": "Parent",
        "variation_theme": "Color",
        "title": "AB Crystal Rondelle Beads",
        "country_of_origin": "China",
    }])
    assert not any(item["field"] == "manufacturer" and item["severity"] == "error" for item in validate_intake(path))


def test_store_ops_bead_copy_passes_listing_rules():
    title, bullets, description = make_copy_for_row("AB彩扁碟珠6", "Gold", "6 mm", "", "100")
    rows = apply_variation_title_rules([
        {"parentage_level": "Parent", "sku": "TTCA-DiscBeads", "set_count": "100", "title": title},
        {"parentage_level": "Child", "sku": "TTCA-DiscBeads-Gold-100", "set_count": "100", "title": title, "color": "Gold", "size": "6 mm"},
        {"parentage_level": "Child", "sku": "TTCA-DiscBeads-Pink-100", "set_count": "100", "title": title, "color": "Pink", "size": "6 mm"},
    ])
    for row in rows:
        assert validate_listing_row({**row, "description": description, **{f"bullet_{index}": bullet for index, bullet in enumerate(bullets, 1)}}) == []
