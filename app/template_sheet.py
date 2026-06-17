TEMPLATE_SHEET_NAMES = ("Template", "模板")


def find_template_sheet(workbook):
    for sheet_name in TEMPLATE_SHEET_NAMES:
        if sheet_name in workbook.sheetnames:
            return workbook[sheet_name]
    return None


def template_sheet_names_text():
    return " / ".join(TEMPLATE_SHEET_NAMES)
