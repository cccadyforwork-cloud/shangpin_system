import hashlib
import re
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from .batch_fast_workbench import (
    attach_file as _attach_file,
    build_output_archive as _build_output_archive,
    load_ledger,
    payload as _payload,
    referenced_file as _referenced_file,
    save_ledger,
)
from .paths import DATA_DIR, safe_name


WORKBENCH_DIR = DATA_DIR / "distribution_workbench"
LEDGER_PATH = WORKBENCH_DIR / "ledger.json"
FILES_DIR = WORKBENCH_DIR / "files"
BATCH_ID = "distribution-kaixuan-2026-10-26"
BATCH_NAME = "凯旋 · 10.26"
OWNER = "凯旋"
STORE_ID = "2店"
OWNER_ORDER = ("cccady", "图图", "凯旋")
OWNER_SLUGS = {"cccady": "cccady", "图图": "tutu", "凯旋": "kaixuan"}
STATUS_VALUES = ("待处理", "可上传", "审核中", "已上传", "需修正", "冻结")
GROUP_STATUS = {
    "已上传成功": ("已上传", "已上传成功"),
    "报价缺失": ("需修正", "报价缺失"),
    "冻结的": ("冻结", "冻结的"),
}
ALLOWED_SUFFIXES = {".xlsx", ".xlsm", ".xls"}


def ensure_ledger(path=LEDGER_PATH):
    data = load_ledger(path)
    if data.get("batches"):
        return data
    data = {
        "version": 1,
        "updated_at": "",
        "source_archive": "",
        "batches": _owner_placeholders(),
    }
    save_ledger(data, path)
    return data


def import_archive(
    archive_path,
    ledger_path=LEDGER_PATH,
    files_dir=FILES_DIR,
    *,
    owner=OWNER,
    store_id=STORE_ID,
    batch_date="2026-10-26",
    batch_id=None,
    batch_name=None,
):
    archive = Path(archive_path).expanduser().resolve()
    if not archive.is_file() or archive.suffix.lower() != ".zip":
        raise ValueError("请选择有效的铺货资料 ZIP。")

    previous = ensure_ledger(ledger_path)
    owner = str(owner or "").strip()
    store_id = str(store_id or "").strip()
    if owner not in OWNER_ORDER:
        raise ValueError("负责人只能选择 cccady、图图或凯旋。")
    if store_id not in {"1店", "2店"}:
        raise ValueError("店铺只能选择 1店或 2店。")
    date_text = str(batch_date or "").strip()
    date_slug = date_text.replace("/", "-")
    short_date = date_text[5:].replace("-", ".") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text) else date_text
    target_batch_id = batch_id or f"distribution-{OWNER_SLUGS[owner]}-{date_slug}"
    target_batch_name = batch_name or f"{owner} · {short_date}"
    previous_batch = next(
        (item for item in previous.get("batches", []) if item.get("id") == target_batch_id),
        {},
    )
    previous_rows = {}
    for row in previous_batch.get("rows", []):
        for key in (row.get("source_member"), row.get("product_name")):
            if key:
                previous_rows[str(key)] = row
    rows = []
    imported_at = datetime.now().astimezone().isoformat(timespec="seconds")
    target_root = Path(files_dir) / safe_name(target_batch_id)

    with zipfile.ZipFile(archive) as source:
        members = [
            info for info in source.infolist()
            if not info.is_dir() and PurePosixPath(_decoded_name(info)).suffix.lower() in ALLOWED_SUFFIXES
        ]
        for index, info in enumerate(members, start=1):
            member_name = _decoded_name(info)
            member_path = PurePosixPath(member_name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("压缩包包含不安全的文件路径。")
            filename = member_path.name
            product_name = _product_name(filename)
            group = member_path.parts[-2] if len(member_path.parts) >= 3 else "待上传"
            status, default_note = GROUP_STATUS.get(group, ("可上传", ""))
            row_prefix = OWNER_SLUGS[owner][:2].upper()
            row_id = row_prefix + "-" + hashlib.sha256(member_name.encode("utf-8")).hexdigest()[:12].upper()
            target = target_root / safe_name(row_id) / "output_file" / safe_name(filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(info))

            previous_row = previous_rows.get(member_name) or previous_rows.get(product_name, {})
            note = str(previous_row.get("note") or default_note)
            row_status = str(previous_row.get("status") or status)
            if row_status not in STATUS_VALUES:
                row_status = status
            stored = _store_path(target)
            version = _output_version(filename)
            versions = [
                dict(item) for item in previous_row.get("output_versions", [])
                if isinstance(item, dict) and int(item.get("version") or 0) != version and item.get("path")
            ]
            versions.append({"version": version, "path": stored, "added_at": imported_at})
            versions.sort(key=lambda item: int(item["version"]))
            rows.append({
                "id": row_id,
                "product_name": product_name,
                "row_number": index,
                "link": "",
                "competitor_links": [],
                "competitor_html": "",
                "source_template": "",
                "output_file": versions[-1]["path"],
                "output_versions": versions,
                "status": row_status,
                "purchase_status": "",
                "note": note,
                "store_id": store_id,
                "source_group": group,
                "source_member": member_name,
            })

    if not rows:
        raise ValueError("压缩包中没有 xlsx、xlsm 或 xls 文件。")
    target_batch = {
        "id": target_batch_id,
        "name": target_batch_name,
        "owner": owner,
        "stores": [store_id],
        "source_archive": archive.name,
        "rows": rows,
    }
    batches = [
        batch for batch in previous.get("batches", [])
        if batch.get("id") != target_batch_id
        and not (batch.get("id") == f"distribution-{OWNER_SLUGS[owner]}" and not batch.get("rows"))
    ]
    batches.append(target_batch)
    data = dict(previous)
    data.update({"version": 1, "updated_at": "", "source_archive": archive.name})
    data["batches"] = _ordered_batches(batches)
    save_ledger(data, ledger_path)
    return {
        "ok": True,
        "count": len(rows),
        "archive": archive.name,
        "batch_id": target_batch_id,
        "owner": owner,
        "store_id": store_id,
    }


def payload(ledger_path=LEDGER_PATH):
    ensure_ledger(ledger_path)
    data = _payload(ledger_path)
    data["statuses"] = list(STATUS_VALUES)
    data["source_archive"] = load_ledger(ledger_path).get("source_archive", "")
    return data


def update_row(batch_id, row_id, fields, ledger_path=LEDGER_PATH):
    data = ensure_ledger(ledger_path)
    batch = next((item for item in data.get("batches", []) if item.get("id") == batch_id), None)
    if batch is None:
        raise ValueError("找不到批次。")
    row = next((item for item in batch.get("rows", []) if item.get("id") == row_id), None)
    if row is None:
        raise ValueError("找不到产品行。")
    for key, value in (fields or {}).items():
        if key not in {"status", "note"}:
            continue
        text = str(value or "").strip()
        if key == "status" and text not in STATUS_VALUES:
            raise ValueError("状态值不正确。")
        row[key] = text
    save_ledger(data, ledger_path)
    return row


def attach_file(batch_id, row_id, field, filename, source, ledger_path=LEDGER_PATH, files_dir=FILES_DIR):
    return _attach_file(batch_id, row_id, field, filename, source, ledger_path, files_dir)


def referenced_file(path_value, ledger_path=LEDGER_PATH, files_dir=FILES_DIR):
    return _referenced_file(path_value, ledger_path, files_dir)


def build_output_archive(batch_id, ledger_path=LEDGER_PATH):
    return _build_output_archive(batch_id, ledger_path)


def _decoded_name(info):
    name = info.filename
    if info.flag_bits & 0x800:
        return name
    try:
        return name.encode("cp437").decode("gb18030")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def _product_name(filename):
    stem = Path(filename).stem
    return re.sub(r"V\d+(?:_已改FOR ADULT)?$", "", stem, flags=re.I)


def _output_version(filename):
    match = re.search(r"V(\d+)(?:_已改FOR ADULT)?(?=\.[^.]+$)", filename, re.I)
    return int(match.group(1)) if match else 1


def _store_path(path):
    from .paths import ROOT

    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _owner_placeholders():
    return [
        {
            "id": f"distribution-{OWNER_SLUGS[owner]}",
            "name": owner,
            "owner": owner,
            "stores": ["1店", "2店"],
            "rows": [],
        }
        for owner in OWNER_ORDER
    ]


def _ordered_batches(batches):
    result = list(batches)
    present_owners = {str(item.get("owner") or "") for item in result}
    for placeholder in _owner_placeholders():
        if placeholder["owner"] not in present_owners:
            result.append(placeholder)
    owner_index = {owner: index for index, owner in enumerate(OWNER_ORDER)}
    return sorted(
        result,
        key=lambda item: (
            owner_index.get(str(item.get("owner") or ""), len(owner_index)),
            str(item.get("id") or ""),
        ),
    )

