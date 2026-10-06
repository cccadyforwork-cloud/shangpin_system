from app.template_validator import PRODUCT_TYPE_PARENT_REQUIRED_FIELDS


def test_bracelet_backend_required_parent_measurements_are_registered():
    assert PRODUCT_TYPE_PARENT_REQUIRED_FIELDS["BRACELET"] == {
        "Item Length End to End": "item_length[marketplace_id=ATVPDKIKX0DER]#1.value",
        "Item Weight": "item_weight[marketplace_id=ATVPDKIKX0DER]#1.value",
        "Item Length": "item_dimensions[marketplace_id=ATVPDKIKX0DER]#1.length.value",
        "Item Width": "item_dimensions[marketplace_id=ATVPDKIKX0DER]#1.width.value",
        "Item Height": "item_dimensions[marketplace_id=ATVPDKIKX0DER]#1.height.value",
    }
