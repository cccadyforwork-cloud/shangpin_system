"""Version-guarded, fill-empty-only merge for the default workbench intake sheet.

This endpoint is intentionally separate from the human-facing save-intake flow. It
never marks a template generated/uploaded, and never changes project_status.json.
"""

import hashlib
import json
import os
import re
import tempfile
import threading
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from openpyxl import load_workbook

from .paths import PROJECTS_DIR


ALLOWED_FIELDS = frozenset({"list_price", "haul_price", "cost", "supplier_link"})
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


class GuardedIntakeConflict(ValueError):
    """The source moved on, or the proposed merge is no longer safe."""


@contextmanager
def project_intake_lock(project_dir):
    key = str(Path(project_dir).resolve())
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(key, threading.RLock())
    with lock:
        lock_path = Path(project_dir) / ".guarded_intake.lock"
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            if os.name == "nt":
                import msvcrt
                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha_file(path):
    return _sha_bytes(Path(path).read_bytes())


def _safe_project(project_ref, projects_root):
    prefix = "data/projects/"
    if not isinstance(project_ref, str) or not project_ref.startswith(prefix):
        raise ValueError("须填写完整的原上品项目 ID。")
    folder = project_ref[len(prefix):]
    if not folder or folder in {".", ".."} or "/" in folder or "\\" in folder or len(folder) > 160:
        raise ValueError("原上品项目 ID 不合法。")
    root = Path(projects_root).resolve()
    path = root / folder
    if path.is_symlink() or not path.is_dir() or not path.resolve().is_relative_to(root):
        raise ValueError("原上品项目目录不存在或超出范围。")
    return path


def _status_and_draft(project_dir):
    status_path = project_dir / "project_status.json"
    if status_path.is_symlink() or not status_path.is_file() or status_path.stat().st_size > 2 * 1024 * 1024:
        raise GuardedIntakeConflict("项目状态文件不存在或不安全，请重新预览。")
    status_bytes = status_path.read_bytes()
    try:
        status = json.loads(status_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise GuardedIntakeConflict("项目状态文件已变化，请重新预览。") from exc
    if not isinstance(status, dict) or status.get("status") not in (None, "not_started"):
        raise GuardedIntakeConflict("原项目已进入后续流程，不能自动补值。")
    if status.get("latest_template"):
        raise GuardedIntakeConflict("原项目已有上传模板引用，不能自动补值。")
    draft_ref = status.get("latest_draft") or status.get("verification_draft")
    if not isinstance(draft_ref, str) or not draft_ref.strip():
        raise GuardedIntakeConflict("原项目没有已确认产品资料。")
    draft_raw = project_dir / draft_ref
    if draft_raw.is_symlink():
        raise GuardedIntakeConflict("产品资料不能是符号链接。")
    draft_path = draft_raw.resolve()
    if not draft_path.is_relative_to(project_dir.resolve()) or draft_path.suffix.lower() != ".xlsx":
        raise GuardedIntakeConflict("产品资料必须是当前项目内的 .xlsx 文件。")
    if not draft_path.is_file() or draft_path.stat().st_size > 30 * 1024 * 1024:
        raise GuardedIntakeConflict("产品资料不存在或超出大小上限。")
    return status_path, status_bytes, draft_path


def _validate_value(field, value):
    if field in {"list_price", "haul_price", "cost"}:
        if isinstance(value, bool):
            raise ValueError(f"{field} 必须是正数。")
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{field} 必须是正数。") from exc
        if not number.is_finite() or number <= 0 or number > 1000000:
            raise ValueError(f"{field} 不在允许的正数范围。")
        return float(number)
    if not isinstance(value, str) or len(value) > 2048 or any(ord(char) < 32 for char in value):
        raise ValueError("采购链接格式不正确。")
    try:
        url = urlsplit(value.strip())
    except ValueError as exc:
        raise ValueError("采购链接格式不正确。") from exc
    if url.scheme not in {"http", "https"} or not url.netloc:
        raise ValueError("采购链接须为 HTTP(S) 地址。")
    return value.strip()


def guarded_merge_intake(payload, projects_root=PROJECTS_DIR):
    """Apply an explicitly approved blank-cell patch only if both source hashes match."""
    if not isinstance(payload, dict) or payload.get("approved") is not True:
        raise ValueError("须明确确认本次只补空白字段。")
    project_ref = payload.get("project_ref")
    project_dir = _safe_project(project_ref, projects_root)
    expected_status = payload.get("expected_status_sha256")
    expected_draft = payload.get("expected_draft_sha256")
    if not all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
               for value in (expected_status, expected_draft)):
        raise ValueError("须提供本次预览的完整状态及产品资料指纹。")
    roster = payload.get("expected_skus")
    changes = payload.get("changes")
    if not isinstance(roster, list) or not roster or len(roster) > 2000 or any(
        not isinstance(sku, str) or not sku.strip() or len(sku) > 160 for sku in roster
    ) or len(roster) != len(set(roster)):
        raise ValueError("须提供唯一、完整的预期 SKU 清单。")
    if not isinstance(changes, list) or not changes or len(changes) > 2000:
        raise ValueError("须提供有限数量的补空值项。")
    normalized = []
    seen = set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("补值项结构不正确。")
        sku, field = change.get("sku"), change.get("field")
        if sku not in roster or field not in ALLOWED_FIELDS or (sku, field) in seen:
            raise ValueError("补值项包含未知 SKU、非允许字段或重复项。")
        seen.add((sku, field))
        normalized.append((sku, field, _validate_value(field, change.get("value"))))

    with project_intake_lock(project_dir):
        status_path, status_bytes, draft_path = _status_and_draft(project_dir)
        if _sha_bytes(status_bytes) != expected_status or _sha_file(draft_path) != expected_draft:
            raise GuardedIntakeConflict("原项目状态或产品资料已变化，请重新预览。")
        book = None
        temp_path = None
        try:
            book = load_workbook(draft_path, read_only=False, data_only=False)
            sheet = book["产品资料"] if "产品资料" in book.sheetnames else book.active
            headers = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[1]]
            names = [name for name in headers if name]
            if len(names) != len(set(names)) or not set(ALLOWED_FIELDS | {"sku"}).issubset(names):
                raise GuardedIntakeConflict("产品资料列已变化，请重新预览。")
            columns = {name: index + 1 for index, name in enumerate(headers) if name}
            rows = {}
            for row_number in range(2, sheet.max_row + 1):
                sku = str(sheet.cell(row_number, columns["sku"]).value or "").strip()
                if not sku or sku.upper().startswith("DEMO"):
                    continue
                if "product_name" in columns and str(sheet.cell(row_number, columns["product_name"]).value or "").strip() == "示例收纳袋":
                    continue
                if sku in rows:
                    raise GuardedIntakeConflict("原产品资料存在重复 SKU，请人工核对。")
                rows[sku] = row_number
            if set(rows) != set(roster):
                raise GuardedIntakeConflict("SKU 清单已变化，请重新预览。")
            for sku, field, value in normalized:
                cell = sheet.cell(rows[sku], columns[field])
                if cell.value is not None and str(cell.value).strip():
                    raise GuardedIntakeConflict(f"{sku} 的 {field} 已有值；不会覆盖。")
                cell.value = value
            fd, temp_name = tempfile.mkstemp(prefix=".guarded_intake_", suffix=".xlsx", dir=draft_path.parent)
            os.close(fd)
            temp_path = Path(temp_name)
            book.save(temp_path)
            book.close()
            book = None
            # The old inode stays recoverable after the atomic replacement.
            if _sha_file(status_path) != expected_status or _sha_file(draft_path) != expected_draft:
                raise GuardedIntakeConflict("保存前来源发生变化，请重新预览。")
            backup_dir = draft_path.parent / ".guarded_intake_backups"
            if backup_dir.is_symlink():
                raise GuardedIntakeConflict("备份目录不能是符号链接。")
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"{expected_draft}.xlsx"
            if backup_path.exists():
                if backup_path.is_symlink() or _sha_file(backup_path) != expected_draft:
                    raise GuardedIntakeConflict("同名备份内容不一致，拒绝覆盖原资料。")
            else:
                old_bytes = draft_path.read_bytes()
                if _sha_bytes(old_bytes) != expected_draft:
                    raise GuardedIntakeConflict("备份期间来源发生变化，请重新预览。")
                try:
                    with backup_path.open("xb") as backup:
                        backup.write(old_bytes)
                        backup.flush()
                        os.fsync(backup.fileno())
                except Exception:
                    backup_path.unlink(missing_ok=True)
                    raise
            if _sha_file(status_path) != expected_status or _sha_file(draft_path) != expected_draft:
                raise GuardedIntakeConflict("备份后来源发生变化，请重新预览。")
            os.replace(temp_path, draft_path)
            temp_path = None
            return {"ok": True, "mode": "guarded_fill_empty", "project_ref": project_ref,
                    "draft_file": str(draft_path), "previous_sha256": expected_draft,
                    "new_sha256": _sha_file(draft_path), "backup_file": str(backup_path),
                    "changed_cells": len(normalized), "status_unchanged": True,
                    "amazon_uploaded": False, "template_generated": False}
        finally:
            if book is not None:
                book.close()
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
