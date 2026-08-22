import re
from pathlib import Path

from .paths import LEGACY_FILLED_TEMPLATE_DIR, safe_name


def version_number(value):
    stem = Path(str(value)).stem
    match = re.search(r"(?:^|[_\-\s])v(\d*)$", stem, re.I)
    if match:
        number = match.group(1)
        return int(number) if number else 1
    match = re.search(r"v(\d+)$", stem, re.I)
    if not match:
        return 0
    number = match.group(1)
    return int(number)


def version_label(number):
    number = int(number or 1)
    return f"V{number}"


def next_template_version(project_dir):
    version_dir = Path(project_dir) / LEGACY_FILLED_TEMPLATE_DIR
    if not version_dir.exists():
        return 1
    versions = [
        version_number(path.name)
        for path in version_dir.iterdir()
        if path.is_file()
        and not path.name.startswith("~$")
        and path.suffix.lower() in {".xlsx", ".xlsm"}
        and "产品资料" not in path.name
        and "自动提炼草稿" not in path.name
    ]
    return (max(versions) + 1) if versions else 1


def versioned_template_path(project_dir, product_name, version=None, suffix=".xlsx"):
    version_dir = Path(project_dir) / LEGACY_FILLED_TEMPLATE_DIR
    version_dir.mkdir(parents=True, exist_ok=True)
    version = next_template_version(project_dir) if version is None else int(version)
    base_name = f"{safe_name(str(product_name))}{version_label(version)}{suffix}"
    path = version_dir / base_name
    if not path.exists():
        return path

    index = 2
    while True:
        candidate = version_dir / f"{path.stem}_{index}{path.suffix}"
        if not candidate.exists():
            return candidate
        index += 1
