"""Finish the seven confirmed 1店 parent/child Amazon templates."""

from pathlib import Path

from openpyxl import load_workbook

from finalize_2026_10_14_first_three import fields, set_copy, set_field


OUTPUT = Path(__file__).resolve().parent.parent / "generated/2026-10-14-cady_1店_其余七品"


def open_template(filename):
    path = OUTPUT / filename
    workbook = load_workbook(path, keep_vba=True)
    sheet = workbook["Template"]
    return path, workbook, sheet, fields(sheet)


def save(path, workbook):
    workbook.save(path)
    workbook.close()


def put(sheet, columns, row, key, value):
    set_field(sheet, columns, row, key, value)


def matching_field(sheet, columns, row, predicate, value):
    matches = [col for key, col in columns.items() if predicate(key)]
    if len(matches) != 1:
        raise ValueError(f"Expected one matching field, got {len(matches)}")
    sheet.cell(row, matches[0]).value = value


def measuring_set():
    path, workbook, sheet, columns = open_template("叠放式量杯量勺套装V1.xlsm")
    title = "10 Pcs Stackable Measuring Cups and Spoons with Stainless Steel Handles, Nesting Kitchen Tools for Cooking and Baking, Black"
    description = "A 10 piece black set of stackable measuring cups and spoons for cooking and baking. The pieces have plastic bodies and stainless steel handles. The nesting format helps keep the set together in kitchen storage."
    bullets = [
        "The set contains 10 measuring cups and spoons for kitchen preparation.",
        "Plastic measuring pieces have stainless steel handles and a black finish.",
        "Stackable pieces nest together to help organize kitchen storage.",
        "Use the cups and spoons when measuring ingredients for cooking or baking.",
        "Check the 10 piece set and listed capacity before ordering.",
    ]
    for row in (7, 8):
        set_copy(sheet, columns, row, title, description, bullets)
    for key, value in [
        ("model_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Measuring Cups and Spoons Set"),
        ("size[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "10 Piece Set"),
        ("care_instructions[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Hand Wash"),
        ("capacity[marketplace_id=ATVPDKIKX0DER]#1.value", 10),
        ("capacity[marketplace_id=ATVPDKIKX0DER]#1.unit", "Cups"),
        ("included_components[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "10 Measuring Cups and Spoons"),
    ]:
        put(sheet, columns, 8, key, value)
    save(path, workbook)


def floral_cards():
    path, workbook, sheet, columns = open_template("3D花束茶杯弹出贺卡3款V1.xlsm")
    entries = [
        (7, "3D Floral Pop Up Greeting Cards with Envelopes, Christmas Teacup, Poinsettia and Pink Blossom, Multiple Colors Available", "Choose one of three floral pop up greeting card designs. The selected design is supplied as one card with an envelope. Options include Christmas Teacup, Christmas Poinsettia, and Pink Blossom Teacup.", None),
        (8, "3D Christmas Floral Teacup Pop Up Greeting Card with Envelope, Bouquet Holiday Card for Women, Mom and Friends", "One Christmas floral teacup pop up greeting card with an envelope. The bouquet and teacup design suits holiday greetings and seasonal display.", "Christmas Teacup"),
        (9, "3D Christmas Poinsettia Pop Up Greeting Card with Envelope, Floral Bouquet Vase Design for Holiday Greetings", "One Christmas poinsettia floral bouquet pop up greeting card with an envelope. The selected design features a holiday vase arrangement.", "Christmas Poinsettia"),
        (10, "3D Pink Cherry Blossom Tulip Teacup Pop Up Greeting Card with Envelope for Birthday and Romantic Occasions", "One pink cherry blossom and tulip teacup pop up greeting card with an envelope. The floral design suits birthday and personal greetings.", "Pink Blossom Teacup"),
    ]
    for row, title, description, set_name in entries:
        bullets = [
            "A 3D floral pop up design opens from a flat greeting card format.",
            "The selected floral design is printed and assembled in paper.",
            "One greeting card and one envelope are included in the selected option.",
            "Choose the design that matches the intended holiday or personal occasion.",
            "Check the selected Christmas Teacup, Poinsettia, or Pink Blossom Teacup design before ordering.",
        ]
        set_copy(sheet, columns, row, title, description, bullets)
        if set_name:
            put(sheet, columns, row, "set_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", set_name)
    save(path, workbook)


def butterfly_card():
    path, workbook, sheet, columns = open_template("3D紫色蝴蝶礼盒贺卡V1.xlsm")
    title = "Purple Butterfly 3D Pop Up Card Box with Envelope, Romantic Greeting Card for Anniversaries and Special Occasions"
    description = "A purple butterfly 3D pop up greeting card box with an envelope. The butterfly design is intended for personal greetings and special occasions. One card design is supplied in this selected option."
    bullets = [
        "Purple butterfly design opens into a three dimensional card box.",
        "Paper greeting card construction suits personal messages and display.",
        "One selected card design comes with an envelope.",
        "The butterfly motif can be used for anniversaries and other occasions.",
        "Check the purple butterfly design before ordering this card.",
    ]
    for row in (7, 8):
        set_copy(sheet, columns, row, title, description, bullets)
    save(path, workbook)


def carriage_card():
    path, workbook, sheet, columns = open_template("3D圣诞马车贺卡V1.xlsm")
    title = "3D Christmas Carriage Pop Up Greeting Card with Envelope, Vintage Royal Santa Holiday Table Decor for Friends and Family"
    description = "A 3D Christmas carriage pop up greeting card with an envelope. The vintage royal Santa carriage scene is designed for holiday greetings and seasonal table display. One card is supplied in the selected option."
    bullets = [
        "A carriage scene opens into a three dimensional Christmas card.",
        "The vintage royal Santa design suits seasonal holiday greetings.",
        "One pop up card and its envelope are included.",
        "The opened card may be displayed on a holiday table or shelf.",
        "Check the Christmas carriage design and included envelope before ordering.",
    ]
    for row in (7, 8):
        set_copy(sheet, columns, row, title, description, bullets)
    put(sheet, columns, 8, "color[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Multicolor")
    put(sheet, columns, 8, "set_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Christmas Carriage")
    save(path, workbook)


def birthday_card():
    path, workbook, sheet, columns = open_template("3D生日弹出贺卡V1.xlsm")
    title = "Happy Birthday 3D Pop Up Greeting Card with Envelope, Blank Note Card for Birthday Celebrations and Party Invitations"
    description = "A 3D Happy Birthday pop up greeting card with a blank note area and an envelope. The card can be used for birthday greetings or party invitations. One card is supplied in the selected option."
    bullets = [
        "The 3D pop up format creates a birthday greeting display when opened.",
        "A blank note area leaves room for a personal message.",
        "One birthday card and one envelope are included.",
        "Use the card for a birthday celebration or invitation.",
        "Check the selected birthday pop up design before ordering.",
    ]
    for row in (7, 8):
        set_copy(sheet, columns, row, title, description, bullets)
    put(sheet, columns, 8, "color[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Multicolor")
    put(sheet, columns, 8, "set_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Pop Up Birthday")
    save(path, workbook)


def dog_calendar():
    path, workbook, sheet, columns = open_template("2027搞怪狗狗挂历V1.xlsm")
    title = "2027 Wacky Dogs Wall Calendar, 12 Month Monthly Planner with Twin Wire Spiral Binding and Large Writable Blocks, US Holidays"
    description = "A 2027 wall calendar with wacky dog images across 12 months. Twin wire spiral binding supports hanging, and the monthly pages provide large blocks for handwritten notes. The calendar lists US holidays."
    bullets = [
        "The 2027 calendar covers 12 monthly planning pages.",
        "Wacky dog images provide the calendar's visual theme.",
        "Twin wire spiral binding supports wall hanging and page turning.",
        "Large monthly date blocks leave space for handwritten plans.",
        "US holidays are listed on the 2027 calendar pages.",
    ]
    for row in (7, 8):
        set_copy(sheet, columns, row, title, description, bullets)
    put(sheet, columns, 8, "color[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Multicolor")
    put(sheet, columns, 8, "set_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Wacky Dogs 2027")
    save(path, workbook)


def sun_moon_box():
    path, workbook, sheet, columns = open_template("太阳月亮图案金属收纳盒V1.xlsm")
    title = "Vintage Sun and Moon Plastic Storage Box, Matte Black Matchbox Style Container with Celestial Design for Small Item Storage"
    description = "A small plastic storage box with a matte black finish and a vintage sun and moon design. The matchbox-style form holds small items. One selected box is supplied."
    bullets = [
        "The small storage box features a vintage sun and moon motif.",
        "Plastic construction has a matte black appearance.",
        "The matchbox style form is suitable for small item storage.",
        "One box is included in the selected option.",
        "Check the sun and moon design, black color, and listed size before ordering.",
    ]
    for row in (7, 8):
        set_copy(sheet, columns, row, title, description, bullets)
        put(sheet, columns, row, "material[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Plastic")
    for key, value in [
        ("model_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Sun and Moon Storage Box"),
        ("special_feature[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Lightweight"),
        ("unit_count[marketplace_id=ATVPDKIKX0DER]#1.value", 1),
        ("unit_count[marketplace_id=ATVPDKIKX0DER]#1.type[language_tag=en_US].value", "Count"),
        ("included_components[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "1 Sun and Moon Storage Box"),
        ("closure[marketplace_id=ATVPDKIKX0DER]#1.type[language_tag=en_US]#1.value", "Sliding"),
        ("set_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value", "Sun and Moon"),
        ("number_of_boxes[marketplace_id=ATVPDKIKX0DER]#1.value", 1),
    ]:
        put(sheet, columns, 8, key, value)
    for key, col in columns.items():
        if key.startswith("item_length_width_height["):
            if ".length.value" in key:
                sheet.cell(8, col).value = 2.36
            elif ".width.value" in key:
                sheet.cell(8, col).value = 1.3
            elif ".height.value" in key:
                sheet.cell(8, col).value = 0.39
            elif key.endswith(".unit"):
                sheet.cell(8, col).value = "Inches"
    save(path, workbook)


if __name__ == "__main__":
    measuring_set()
    floral_cards()
    butterfly_card()
    carriage_card()
    birthday_card()
    dog_calendar()
    sun_moon_box()
