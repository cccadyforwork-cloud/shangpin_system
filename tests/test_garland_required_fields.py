import unittest

from app.template_validator import (
    PRODUCT_TYPE_CONDITIONAL_FIELDS,
    _is_parent_optional_required_field,
)


class GarlandRequiredFieldsTest(unittest.TestCase):
    def test_garland_dynamic_required_fields_are_checked(self):
        self.assertEqual(
            PRODUCT_TYPE_CONDITIONAL_FIELDS["GARLAND"],
            {
                "Model Name": "model_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
                "Included Components": "included_components[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value",
                "Required Assembly": "is_assembly_required[marketplace_id=ATVPDKIKX0DER]#1.value",
            },
        )

    def test_garland_dynamic_required_fields_remain_optional_on_parent_rows(self):
        for field_name in PRODUCT_TYPE_CONDITIONAL_FIELDS["GARLAND"].values():
            with self.subTest(field_name=field_name):
                self.assertTrue(_is_parent_optional_required_field(field_name))


if __name__ == "__main__":
    unittest.main()
