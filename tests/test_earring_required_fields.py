from app.template_validator import PRODUCT_TYPE_CONDITIONAL_FIELDS
from app.template_writer import _stable_field_default


def test_earring_backend_required_stone_fields_are_registered():
    assert PRODUCT_TYPE_CONDITIONAL_FIELDS["EARRING"] == {
        "Stone Creation Method": "stones[marketplace_id=ATVPDKIKX0DER]#1.creation_method[language_tag=en_US].value",
        "Stone Treatment Method": "stones[marketplace_id=ATVPDKIKX0DER]#1.treatment_method[language_tag=en_US].value",
    }


def test_no_gemstone_earring_defaults_match_template_valid_values():
    row = {"product_type": "EARRING"}
    fields = PRODUCT_TYPE_CONDITIONAL_FIELDS["EARRING"]

    assert _stable_field_default(fields["Stone Creation Method"], row) == "Unknown"
    assert _stable_field_default(fields["Stone Treatment Method"], row) == "Not Treated"
