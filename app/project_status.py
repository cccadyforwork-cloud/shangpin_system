import json
from datetime import date, datetime
from pathlib import Path

from .workbook_io import read_intake_rows


STATUS_FILE = "project_status.json"


def status_path(project_dir):
    return Path(project_dir) / STATUS_FILE


def load_project_status(project_dir):
    path = status_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_project_status(project_dir, status):
    path = status_path(project_dir)
    current = load_project_status(project_dir)
    for key, value in status.items():
        if value is None:
            current.pop(key, None)
        else:
            current[key] = value
    current["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(
        json.dumps(current, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    return path


def mark_uploaded_success(project_dir, product_name, latest_template, sku_count=None, uploaded_at=None, notes=""):
    project_dir = Path(project_dir)
    template_path = Path(latest_template)
    if template_path.is_absolute():
        try:
            template_path = template_path.relative_to(project_dir)
        except ValueError:
            pass

    return save_project_status(project_dir, {
        "product_name": product_name,
        "status": "uploaded_success",
        "latest_template": str(template_path),
        "sku_count": sku_count,
        "uploaded_at": uploaded_at or date.today().isoformat(),
        "notes": notes,
    })


def infer_latest_template(project_dir):
    project_dir = Path(project_dir)
    candidates = []
    for folder in ("05_填表版本", "04_模板原件"):
        template_dir = project_dir / folder
        if not template_dir.exists():
            continue
        for path in template_dir.glob("*"):
            if path.name.startswith("~$"):
                continue
            if path.suffix.lower() not in {".xlsx", ".xlsm"}:
                continue
            if "产品资料" in path.name or "自动提炼草稿" in path.name:
                continue
            candidates.append(path)
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[0]


def infer_product_name(project_dir, explicit_name=""):
    if explicit_name:
        return explicit_name
    status = load_project_status(project_dir)
    if status.get("product_name"):
        return status["product_name"]
    name = Path(project_dir).name
    parts = name.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[1]
    return name


def infer_sku_count(project_dir, explicit_count=None):
    if explicit_count is not None:
        return explicit_count
    status = load_project_status(project_dir)
    for key in ("sku_count", "verification_sku_count"):
        if status.get(key):
            return status[key]
    project_dir = Path(project_dir)
    draft_dir = project_dir / "07_上架备注"
    candidates = sorted(
        [
            path for path in draft_dir.glob("*.xlsx")
            if not path.name.startswith("~$")
            and ("自动提炼草稿" in path.name or "产品资料" in path.name)
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        try:
            rows = read_intake_rows(path)
        except Exception:
            continue
        if rows:
            return len(rows)
    return None
