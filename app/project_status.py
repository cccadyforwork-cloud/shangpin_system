import json
from datetime import date, datetime
from pathlib import Path


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
