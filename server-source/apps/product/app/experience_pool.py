"""Private, appendable experience store for Amazon listing work.

The pool stores evidence; it never bypasses the current writer, validator or
red-field scanner.  Imported conversation excerpts remain ``needs_review``
until a successful upload or current validation confirms them.
"""

import hashlib
import json
import mimetypes
import re
import sqlite3
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from .paths import ROOT


POOL_PATH = ROOT / "上品经验池.sqlite3"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv"}
ARTIFACT_PREFIXES = (
    "experience_archive/task_transcripts/",
    "server_runtime/data/success_templates/",
    "server_runtime/outputs/",
    "server_runtime/data/error_learnings.json",
    "server_runtime/data/success_template_rules.json",
    "01_经验手册/",
    "02_结构化规则/",
)


def connect(path=POOL_PATH):
    database = sqlite3.connect(Path(path))
    database.row_factory = sqlite3.Row
    database.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            package_name TEXT NOT NULL,
            sha256 TEXT NOT NULL UNIQUE,
            imported_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS records (
            record_key TEXT PRIMARY KEY,
            source_id INTEGER,
            kind TEXT NOT NULL,
            title TEXT,
            asin TEXT,
            product_types TEXT,
            error_codes TEXT,
            review_status TEXT NOT NULL,
            body TEXT,
            data_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        CREATE INDEX IF NOT EXISTS idx_records_asin ON records(asin);
        CREATE INDEX IF NOT EXISTS idx_records_kind ON records(kind);
        CREATE TABLE IF NOT EXISTS artifacts (
            sha256 TEXT PRIMARY KEY,
            source_id INTEGER,
            archive_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            mime_type TEXT,
            content BLOB NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        CREATE TABLE IF NOT EXISTS fill_events (
            id TEXT PRIMARY KEY,
            asin TEXT,
            msku TEXT,
            product_name TEXT,
            product_type TEXT,
            template_sha256 TEXT,
            outcome TEXT NOT NULL,
            error_codes TEXT,
            evidence_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_fill_events_asin ON fill_events(asin);
        CREATE INDEX IF NOT EXISTS idx_fill_events_product_type ON fill_events(product_type);
        """
    )
    return database


def import_package(zip_path, pool_path=POOL_PATH):
    archive_path = Path(zip_path).expanduser().resolve()
    package_sha = _file_sha256(archive_path)
    now = _now()
    database = connect(pool_path)
    cursor = database.execute(
        "INSERT OR IGNORE INTO sources(package_name, sha256, imported_at) VALUES(?,?,?)",
        (archive_path.name, package_sha, now),
    )
    source = database.execute("SELECT id FROM sources WHERE sha256=?", (package_sha,)).fetchone()
    source_id = source["id"]
    counts = {"records": 0, "artifacts": 0}
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        knowledge_bundle = not any("experience_archive/" in name or "server_runtime/" in name for name in names)
        candidate_name = next((name for name in names if name.endswith("experience_archive/candidate_rules.json")), None)
        if candidate_name:
            for item in json.loads(archive.read(candidate_name).decode("utf-8")):
                text = str(item.get("excerpt") or "")
                _insert_record(
                    database,
                    source_id,
                    record_key=f"candidate:{item.get('candidate_id')}",
                    kind="candidate_experience",
                    title=str(item.get("task_title") or ""),
                    body=text,
                    product_types=item.get("product_types") or [],
                    error_codes=item.get("error_codes") or [],
                    review_status=str(item.get("status") or "needs_review"),
                    data=item,
                )
                counts["records"] += 1
        task_name = next((name for name in names if name.endswith("experience_archive/task_index.json")), None)
        if task_name:
            for item in json.loads(archive.read(task_name).decode("utf-8")):
                _insert_record(
                    database,
                    source_id,
                    record_key=f"task:{item.get('id')}",
                    kind="historical_task",
                    title=str(item.get("title") or ""),
                    body=str(item.get("title") or ""),
                    review_status="reference_only",
                    data=item,
                )
                counts["records"] += 1
        for name in names:
            relative = _relative_archive_name(name)
            if not relative or name.endswith("/") or not _wanted_artifact(relative, knowledge_bundle=knowledge_bundle):
                continue
            content = archive.read(name)
            digest = hashlib.sha256(content).hexdigest()
            database.execute(
                "INSERT OR IGNORE INTO artifacts(sha256,source_id,archive_path,filename,mime_type,content,created_at) VALUES(?,?,?,?,?,?,?)",
                (digest, source_id, relative, Path(relative).name, mimetypes.guess_type(relative)[0] or "application/octet-stream", content, now),
            )
            counts["artifacts"] += 1
            suffix = Path(relative).suffix.lower()
            if suffix in TEXT_SUFFIXES and "task_transcripts/" not in relative:
                body = _decode_text(content)
                if body:
                    kind = "validated_reference" if ("success" in relative.lower() or "成功" in relative) else "reference_document"
                    _insert_record(
                        database,
                        source_id,
                        record_key=f"artifact:{digest}",
                        kind=kind,
                        title=Path(relative).name,
                        body=body,
                        review_status="validated_reference" if kind == "validated_reference" else "reference_only",
                        data={"archive_path": relative, "sha256": digest},
                    )
                    counts["records"] += 1
    database.commit()
    totals = statistics(database)
    database.close()
    return {"package": archive_path.name, **counts, **totals}


def lookup(asin="", product_name="", product_type="", limit=12, pool_path=POOL_PATH):
    path = Path(pool_path)
    if not path.exists():
        return []
    database = connect(path)
    clauses = []
    parameters = []
    asin = str(asin or "").strip().upper()
    product_type = str(product_type or "").strip().upper()
    if asin:
        clauses.extend(["asin = ?", "body LIKE ?", "data_json LIKE ?"])
        parameters.extend([asin, f"%{asin}%", f"%{asin}%"])
    if product_type:
        clauses.extend(["product_types LIKE ?", "body LIKE ?"])
        parameters.extend([f"%{product_type}%", f"%{product_type}%"])
    words = [word for word in re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{2,}", str(product_name or ""))[:5]]
    for word in words:
        clauses.extend(["title LIKE ?", "body LIKE ?"])
        parameters.extend([f"%{word}%", f"%{word}%"])
    if not clauses:
        database.close()
        return []
    query = "SELECT record_key,kind,title,asin,product_types,error_codes,review_status,substr(body,1,500) AS excerpt FROM records WHERE " + " OR ".join(clauses) + " ORDER BY CASE review_status WHEN 'validated' THEN 0 WHEN 'validated_reference' THEN 1 WHEN 'reference_only' THEN 2 ELSE 3 END, created_at DESC LIMIT ?"
    rows = [dict(row) for row in database.execute(query, (*parameters, int(limit))).fetchall()]
    database.close()
    return rows


def lookup_many_asins(asins, limit_per_asin=5, pool_path=POOL_PATH):
    path = Path(pool_path)
    values = sorted({str(value or "").strip().upper() for value in asins if str(value or "").strip()})
    if not path.exists() or not values:
        return {value: [] for value in values}
    database = connect(path)
    result = {}
    for asin in values:
        rows = database.execute(
            "SELECT record_key,kind,title,review_status,substr(body,1,300) AS excerpt FROM records WHERE asin=? OR body LIKE ? OR data_json LIKE ? ORDER BY CASE review_status WHEN 'validated' THEN 0 WHEN 'validated_reference' THEN 1 WHEN 'reference_only' THEN 2 ELSE 3 END LIMIT ?",
            (asin, f"%{asin}%", f"%{asin}%", int(limit_per_asin)),
        ).fetchall()
        result[asin] = [dict(row) for row in rows]
    database.close()
    return result


def record_fill_event(*, asin="", msku="", product_name="", product_type="", template_path="", outcome, error_codes=None, evidence=None, pool_path=POOL_PATH):
    template = Path(template_path) if template_path else None
    template_sha = _file_sha256(template) if template and template.is_file() else ""
    database = connect(pool_path)
    event_id = uuid.uuid4().hex
    database.execute(
        "INSERT INTO fill_events(id,asin,msku,product_name,product_type,template_sha256,outcome,error_codes,evidence_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            event_id,
            str(asin or "").upper(),
            str(msku or ""),
            str(product_name or ""),
            str(product_type or "").upper(),
            template_sha,
            str(outcome),
            json.dumps(error_codes or [], ensure_ascii=False),
            json.dumps(evidence or {}, ensure_ascii=False),
            _now(),
        ),
    )
    database.commit()
    database.close()
    return event_id


def statistics(database_or_path=POOL_PATH):
    owns = not isinstance(database_or_path, sqlite3.Connection)
    database = connect(database_or_path) if owns else database_or_path
    result = {
        "source_count": database.execute("SELECT count(*) FROM sources").fetchone()[0],
        "record_count": database.execute("SELECT count(*) FROM records").fetchone()[0],
        "artifact_count": database.execute("SELECT count(*) FROM artifacts").fetchone()[0],
        "fill_event_count": database.execute("SELECT count(*) FROM fill_events").fetchone()[0],
    }
    if owns:
        database.close()
    return result


def _insert_record(database, source_id, *, record_key, kind, title="", body="", product_types=None, error_codes=None, review_status, data=None):
    asin_match = re.search(r"\b(B0[A-Z0-9]{8})\b", f"{title}\n{body}", re.I)
    database.execute(
        "INSERT OR REPLACE INTO records(record_key,source_id,kind,title,asin,product_types,error_codes,review_status,body,data_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            record_key,
            source_id,
            kind,
            title,
            asin_match.group(1).upper() if asin_match else "",
            json.dumps(product_types or [], ensure_ascii=False),
            json.dumps(error_codes or [], ensure_ascii=False),
            review_status,
            body,
            json.dumps(data or {}, ensure_ascii=False),
            _now(),
        ),
    )


def _relative_archive_name(name):
    parts = Path(name).parts
    return Path(*parts[1:]).as_posix() if len(parts) > 1 else name


def _wanted_artifact(relative, *, knowledge_bundle=False):
    if knowledge_bundle:
        return Path(relative).suffix.lower() in {".md", ".json", ".xlsx", ".xlsm"}
    return any(relative.startswith(prefix) for prefix in ARTIFACT_PREFIXES)


def _decode_text(content):
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def _file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")
