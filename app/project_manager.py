from datetime import datetime
from pathlib import Path
import shutil

from .paths import PRODUCT_DETAIL_DIR, PROJECTS_DIR, PROJECT_FOLDERS, ensure_base_dirs, safe_name
from .project_status import load_project_status
from .workbook_io import create_intake_workbook


def create_project(project_name):
    ensure_base_dirs()
    stamp = datetime.now().strftime("%Y%m%d")
    folder_name = f"{stamp}_{safe_name(project_name)}"
    project_dir = PROJECTS_DIR / folder_name
    project_dir.mkdir(parents=True, exist_ok=True)

    for folder in PROJECT_FOLDERS:
        (project_dir / folder).mkdir(exist_ok=True)

    intake_path = project_dir / PRODUCT_DETAIL_DIR / f"{safe_name(project_name)}_产品资料.xlsx"
    if not intake_path.exists():
        create_intake_workbook(intake_path)

    readme_path = project_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "\n".join([
                f"# {project_name}",
                "",
                "## 最简执行顺序",
                "",
                "1. 收资料",
                "2. 判断 Generic 还是品牌路线",
                "3. 解析模板",
                "4. 填基础字段",
                "5. 换算尺寸重量",
                "6. 写标题、五点、描述",
                "7. 上传前自检",
                "8. 上传",
                "9. 看 processing summary",
                "10. 按错误码修下一版",
                ""
            ]),
            encoding="utf-8"
        )

    return project_dir, intake_path


def list_projects():
    ensure_base_dirs()
    return sorted([path for path in PROJECTS_DIR.iterdir() if path.is_dir()])


def delete_project(project_dir):
    ensure_base_dirs()
    path = Path(project_dir).resolve()
    projects_dir = PROJECTS_DIR.resolve()
    try:
        path.relative_to(projects_dir)
    except ValueError as exc:
        raise ValueError("项目路径必须在 data/projects 下。") from exc
    if path == projects_dir:
        raise ValueError("不能删除项目根目录。")
    if not path.exists():
        raise ValueError("项目不存在。")
    if not path.is_dir():
        raise ValueError("项目路径不是文件夹。")
    shutil.rmtree(path)
    return path


def list_project_summaries():
    summaries = []
    for project_dir in list_projects():
        status = load_project_status(project_dir)
        summaries.append({
            "project_dir": project_dir,
            "folder": project_dir.name,
            "product_name": status.get("product_name") or _name_from_folder(project_dir.name),
            "status": status.get("status") or "not_started",
            "sku_count": status.get("sku_count") or status.get("verification_sku_count") or "",
            "template_error_count": status.get("template_error_count"),
            "latest_draft": status.get("latest_draft") or status.get("verification_draft") or "",
            "latest_template": status.get("latest_template") or status.get("verification_template") or "",
            "source_template": status.get("source_template") or status.get("verification_source_template") or "",
            "latest_check_report": status.get("latest_check_report") or status.get("verification_check_report") or "",
            "latest_failure_report": status.get("latest_failure_report") or "",
            "latest_fix_report": status.get("latest_fix_report") or "",
            "failed_template": status.get("failed_template") or "",
            "pending_next_version": status.get("pending_next_version") or "",
            "updated_at": status.get("updated_at") or "",
            "uploaded_at": status.get("uploaded_at") or "",
            "notes": status.get("notes") or "",
            "blocked_reason": status.get("blocked_reason") or "",
        })
    return sorted(summaries, key=_project_sort_key)


def _project_sort_key(item):
    is_waiting = item.get("status") != "uploaded_success"
    return (0 if is_waiting else 1, -_updated_timestamp(item.get("updated_at")))


def _updated_timestamp(value):
    if not value:
        return 0
    try:
        return datetime.fromisoformat(str(value)).timestamp()
    except ValueError:
        return 0


def _name_from_folder(folder_name):
    parts = folder_name.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[1]
    return folder_name
