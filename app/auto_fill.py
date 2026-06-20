from pathlib import Path

from .analyzer import analyze_project
from .paths import DRAFT_DIRS, LEGACY_FILLED_TEMPLATE_DIR
from .project_status import load_project_status, save_project_status
from .template_validator import validate_template_file
from .template_writer import fill_template, find_template
from .workbook_io import read_intake_rows


def auto_fill_project(project_dir, draft_path=None, template_path=None, output_path=None, force=False):
    project_dir = Path(project_dir)
    status = load_project_status(project_dir)
    if status.get("status") == "uploaded_success" and not force:
        return {
            "skipped": True,
            "reason": "project_already_uploaded",
            "project_dir": project_dir,
            "status": status,
        }

    try:
        draft_path = Path(draft_path) if draft_path else _ensure_draft(project_dir)
        template_path = Path(template_path) if template_path else find_template(project_dir)
    except (FileNotFoundError, ValueError) as exc:
        status_path = save_project_status(project_dir, {
            "status": "blocked",
            "blocked_reason": str(exc),
        })
        return {
            "skipped": False,
            "blocked": True,
            "project_dir": project_dir,
            "status_path": status_path,
            "reason": str(exc),
        }

    output_path = Path(output_path) if output_path else _default_output_path(project_dir, draft_path)

    filled_path, used_draft, used_template, written_fields = fill_template(
        project_dir,
        draft_path=draft_path,
        template_path=template_path,
        output_path=output_path,
    )
    findings, report_path = validate_template_file(filled_path)
    error_count = sum(1 for item in findings if item["severity"] == "error")
    rows = read_intake_rows(used_draft)

    next_status = "ready_for_upload" if error_count == 0 else "needs_manual_fix"
    if status.get("status") == "uploaded_success" and not _is_project_file(project_dir, filled_path):
        status_update = {
            "verification_draft": _relative(project_dir, used_draft),
            "verification_template": str(filled_path),
            "verification_source_template": _relative(project_dir, used_template),
            "verification_check_report": _relative(project_dir, report_path),
            "verification_sku_count": len(rows),
            "verification_written_field_count": len(written_fields),
            "verification_error_count": error_count,
        }
        status_update["last_verification_status"] = next_status
    else:
        status_update = {
            "product_name": rows[0].get("product_name") if rows else project_dir.name,
            "latest_draft": _relative(project_dir, used_draft),
            "latest_template": _relative(project_dir, filled_path),
            "source_template": _relative(project_dir, used_template),
            "latest_check_report": _relative(project_dir, report_path),
            "sku_count": len(rows),
            "written_field_count": len(written_fields),
            "template_error_count": error_count,
            "blocked_reason": None,
        }
        status_update["status"] = next_status

    status_path = save_project_status(project_dir, status_update)

    return {
        "skipped": False,
        "project_dir": project_dir,
        "draft_path": used_draft,
        "template_path": used_template,
        "filled_path": filled_path,
        "report_path": report_path,
        "status_path": status_path,
        "sku_count": len(rows),
        "written_field_count": len(written_fields),
        "error_count": error_count,
        "status": next_status,
    }


def _ensure_draft(project_dir):
    project_dir = Path(project_dir)
    candidates = []
    for folder in DRAFT_DIRS:
        draft_dir = project_dir / folder
        if not draft_dir.exists():
            continue
        candidates.extend([
            path for path in draft_dir.glob("*.xlsx")
            if not path.name.startswith("~$")
            and "产品资料" not in path.name
        ])
    if candidates:
        return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[0]

    draft_path, _report_path = analyze_project(project_dir, None)
    return draft_path


def _default_output_path(project_dir, draft_path):
    project_dir = Path(project_dir)
    draft_path = Path(draft_path)
    product_name = draft_path.stem.replace("_自动提炼草稿", "")
    return project_dir / LEGACY_FILLED_TEMPLATE_DIR / f"{product_name}_autofill.xlsx"


def _relative(project_dir, path):
    project_dir = Path(project_dir)
    path = Path(path)
    try:
        return str(path.relative_to(project_dir))
    except ValueError:
        return str(path)


def _is_project_file(project_dir, path):
    try:
        Path(path).relative_to(Path(project_dir))
        return True
    except ValueError:
        return False
