"""Codex task orchestration for the unified product workbench.

Codex analyzes source material and returns a structured manifest.  Amazon
workbook generation and validation remain deterministic and are always run by
the existing project core.
"""

import importlib.util
import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path

from .batch_fast_prelisting import run_batch_fast_prelisting
from .batch_fast_workbench import LEDGER_PATH, WORKBENCH_DIR, row_context, update_row
from .experience_pool import lookup as lookup_experience
from .experience_pool import record_fill_event
from .paths import ROOT, safe_name


JOBS_PATH = WORKBENCH_DIR / "codex_jobs.json"
TASKS_DIR = WORKBENCH_DIR / "codex_tasks"
ACTIVE_STATUSES = {"queued", "waiting_claim", "analyzing", "generating"}
MAX_USER_REQUEST = 2000
MAX_RESPONSE = 8000

_LOCK = threading.RLock()
_RUNNING = set()


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_jobs(path=JOBS_PATH):
    path = Path(path)
    if not path.exists():
        return {"version": 1, "updated_at": "", "jobs": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("version", 1)
    data.setdefault("updated_at", "")
    data.setdefault("jobs", [])
    return data


def _save_jobs(data, path=JOBS_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def runtime_status():
    installed = importlib.util.find_spec("openai_codex") is not None
    enabled = os.getenv("CODEX_WORKBENCH_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    mode = os.getenv("CODEX_WORKBENCH_MODE", "server").strip().lower()
    if mode == "manual_workers":
        return {
            "installed": installed,
            "enabled": True,
            "ready": True,
            "mode": "manual_workers",
            "message": "等待上品电脑人工领取",
        }
    if not installed:
        message = "服务器尚未安装 Codex 运行组件"
    elif not enabled:
        message = "Codex 尚未完成公司服务器授权"
    else:
        message = "Codex 已启用"
    return {
        "installed": installed,
        "enabled": enabled,
        "ready": installed and enabled,
        "mode": "server",
        "message": message,
    }


def jobs_payload(jobs_path=JOBS_PATH):
    with _LOCK:
        data = _load_jobs(jobs_path)
        changed = False
        for job in data["jobs"]:
            if (
                job.get("execution_mode", "server") == "server"
                and job.get("status") in ACTIVE_STATUSES
                and job.get("id") not in _RUNNING
            ):
                job["status"] = "failed"
                job["message"] = "服务重启中断了这次任务，请重新分析。"
                job["updated_at"] = _now()
                changed = True
        if changed:
            _save_jobs(data, jobs_path)
        latest = {}
        for job in data["jobs"]:
            latest[f"{job.get('batch_id')}::{job.get('row_id')}"] = _public_job(job)
        return {
            "ok": True,
            "runtime": runtime_status(),
            "jobs": [_public_job(job) for job in data["jobs"][-100:]],
            "latest_by_row": latest,
            "updated_at": data.get("updated_at", ""),
        }


def start_analysis(
    batch_id,
    row_id,
    user_request="",
    *,
    jobs_path=JOBS_PATH,
    tasks_dir=TASKS_DIR,
    ledger_path=LEDGER_PATH,
    analyzer=None,
    route_runner=None,
    background=True,
):
    context = row_context(batch_id, row_id, ledger_path=ledger_path)
    missing = _missing_inputs(context["row"])
    request = str(user_request or "").strip()[:MAX_USER_REQUEST]
    with _LOCK:
        data = _load_jobs(jobs_path)
        active = next(
            (
                job
                for job in reversed(data["jobs"])
                if job.get("batch_id") == batch_id
                and job.get("row_id") == row_id
                and job.get("status") in ACTIVE_STATUSES
            ),
            None,
        )
        if active:
            return _public_job(active)
        runtime = runtime_status()
        manual = runtime["mode"] == "manual_workers"
        status = "waiting_claim" if manual else "queued"
        message = "等待上品电脑领取" if manual else "已进入 Codex 分析队列"
        if missing:
            status = "needs_input"
            message = "请先补充：" + "、".join(missing)
        elif analyzer is None and not runtime["ready"]:
            status = "needs_setup"
            message = runtime["message"]
        job = {
            "id": uuid.uuid4().hex,
            "batch_id": str(batch_id),
            "row_id": str(row_id),
            "status": status,
            "execution_mode": "manual_workers" if manual else "server",
            "core_status": "",
            "message": message,
            "user_request": request,
            "thread_id": "",
            "worker_thread_id": "",
            "worker_thread_owner": "",
            "claimed_by": "",
            "claimed_at": "",
            "output_file": "",
            "last_response": "",
            "created_at": _now(),
            "updated_at": _now(),
        }
        data["jobs"].append(job)
        _save_jobs(data, jobs_path)
    if status != "queued":
        return _public_job(job)
    return _launch(
        job["id"],
        context,
        jobs_path=jobs_path,
        tasks_dir=tasks_dir,
        ledger_path=ledger_path,
        analyzer=analyzer,
        route_runner=route_runner,
        background=background,
    )


def continue_analysis(
    job_id,
    user_request="",
    *,
    jobs_path=JOBS_PATH,
    tasks_dir=TASKS_DIR,
    ledger_path=LEDGER_PATH,
    analyzer=None,
    route_runner=None,
    background=True,
):
    with _LOCK:
        data = _load_jobs(jobs_path)
        previous = _find_job(data, job_id)
    context = row_context(previous["batch_id"], previous["row_id"], ledger_path=ledger_path)
    missing = _missing_inputs(context["row"])
    if missing:
        return _update_job(job_id, jobs_path, status="needs_input", message="请先补充：" + "、".join(missing))
    if analyzer is None and not runtime_status()["ready"]:
        return _update_job(job_id, jobs_path, status="needs_setup", message=runtime_status()["message"])
    request = str(user_request or "").strip()[:MAX_USER_REQUEST]
    runtime = runtime_status()
    if runtime["mode"] == "manual_workers":
        return _update_job(
            job_id,
            jobs_path,
            status="waiting_claim",
            message="等待上品电脑领取并继续",
            user_request=request or previous.get("user_request", ""),
            claimed_by="",
            claimed_at="",
        )
    _update_job(
        job_id,
        jobs_path,
        status="queued",
        message="已继续 Codex 分析",
        user_request=request or previous.get("user_request", ""),
    )
    return _launch(
        job_id,
        context,
        jobs_path=jobs_path,
        tasks_dir=tasks_dir,
        ledger_path=ledger_path,
        analyzer=analyzer,
        route_runner=route_runner,
        background=background,
        resume_thread_id=previous.get("thread_id", ""),
    )


def claim_manual_job(job_id, worker_id, *, jobs_path=JOBS_PATH, ledger_path=LEDGER_PATH):
    worker_id = _worker_id(worker_id)
    context = None
    with _LOCK:
        data = _load_jobs(jobs_path)
        job = _find_job(data, job_id)
        if job.get("execution_mode") != "manual_workers":
            raise ValueError("这个任务不是电脑领取模式。")
        claimed_by = str(job.get("claimed_by") or "")
        status = job.get("status")
        if claimed_by and claimed_by != worker_id:
            raise ValueError(f"任务已由 {claimed_by} 领取。")
        if status == "completed":
            raise ValueError("任务已经完成，如需重做请新建任务。")
        if status not in {"waiting_claim", "needs_input", "failed", "analyzing"}:
            raise ValueError("当前任务暂时不能领取。")
        context = row_context(job["batch_id"], job["row_id"], ledger_path=ledger_path)
        missing = _missing_inputs(context["row"])
        if missing:
            job["status"] = "needs_input"
            job["message"] = "请先补充：" + "、".join(missing)
            job["updated_at"] = _now()
            _save_jobs(data, jobs_path)
            raise ValueError(job["message"])
        job["claimed_by"] = worker_id
        job["claimed_at"] = _now()
        job["status"] = "analyzing"
        job["message"] = f"{worker_id} 已领取，正在调用本机 Codex"
        job["updated_at"] = _now()
        _save_jobs(data, jobs_path)
        public = _public_job(job)
    row = context["row"]
    return {
        "ok": True,
        "job": public,
        "task": {
            "asin": row.get("asin") or row.get("id"),
            "link": row.get("link") or "",
            "instructions": job.get("user_request", ""),
            "worker_thread_id": (
                job.get("worker_thread_id", "")
                if job.get("worker_thread_owner") == worker_id
                else ""
            ),
            "files": {
                field: Path(path).name if path else ""
                for field, path in row.get("resolved_files", {}).items()
                if field in {"competitor_html", "source_template"}
            },
        },
    }


def manual_job_file(job_id, worker_id, field, *, jobs_path=JOBS_PATH, ledger_path=LEDGER_PATH):
    if field not in {"competitor_html", "source_template"}:
        raise ValueError("不支持读取这个文件。")
    worker_id = _worker_id(worker_id)
    with _LOCK:
        job = _find_job(_load_jobs(jobs_path), job_id)
        if job.get("claimed_by") != worker_id:
            raise ValueError("这台电脑没有领取该任务。")
    context = row_context(job["batch_id"], job["row_id"], ledger_path=ledger_path)
    path = Path(context["row"]["resolved_files"].get(field) or "")
    if not path.is_file():
        raise ValueError("任务文件不存在。")
    return path


def submit_manual_analysis(
    job_id,
    worker_id,
    response,
    *,
    jobs_path=JOBS_PATH,
    tasks_dir=TASKS_DIR,
    ledger_path=LEDGER_PATH,
    route_runner=None,
):
    worker_id = _worker_id(worker_id)
    with _LOCK:
        job = dict(_find_job(_load_jobs(jobs_path), job_id))
        if job.get("claimed_by") != worker_id:
            raise ValueError("这台电脑没有领取该任务。")
        if job.get("status") not in {"analyzing", "needs_input", "failed"}:
            raise ValueError("当前任务不能提交分析结果。")
    if not isinstance(response, dict):
        raise ValueError("本机 Codex 返回格式不正确。")
    result = response.get("result") if isinstance(response.get("result"), dict) else response
    worker_thread_id = str(response.get("thread_id") or job.get("worker_thread_id") or "")
    _update_job(
        job_id,
        jobs_path,
        worker_thread_id=worker_thread_id,
        worker_thread_owner=worker_id if worker_thread_id else "",
        last_response=json.dumps(result, ensure_ascii=False)[:MAX_RESPONSE],
    )
    if result.get("status") == "needs_input":
        return _update_job(
            job_id,
            jobs_path,
            status="needs_input",
            message=str(result.get("message") or "需要补充商品资料。")[:1000],
        )
    context = row_context(job["batch_id"], job["row_id"], ledger_path=ledger_path)
    task = _manifest_task(result.get("manifest_json"), context)
    return _execute_core(
        job_id,
        job,
        task,
        jobs_path=jobs_path,
        tasks_dir=tasks_dir,
        ledger_path=ledger_path,
        route_runner=route_runner,
    )


def fail_manual_job(job_id, worker_id, message, *, jobs_path=JOBS_PATH):
    worker_id = _worker_id(worker_id)
    with _LOCK:
        job = _find_job(_load_jobs(jobs_path), job_id)
        if job.get("claimed_by") != worker_id:
            raise ValueError("这台电脑没有领取该任务。")
    return _update_job(job_id, jobs_path, status="failed", message=str(message or "本机 Codex 执行失败。")[:1000])


def release_manual_job(job_id, worker_id, *, jobs_path=JOBS_PATH):
    worker_id = _worker_id(worker_id)
    with _LOCK:
        data = _load_jobs(jobs_path)
        job = _find_job(data, job_id)
        if job.get("claimed_by") != worker_id:
            raise ValueError("只有领取任务的电脑可以释放。")
        if job.get("status") in {"generating", "completed"}:
            raise ValueError("写表中或已完成的任务不能释放。")
        job["claimed_by"] = ""
        job["claimed_at"] = ""
        job["status"] = "waiting_claim"
        job["message"] = "任务已释放，等待上品电脑领取"
        job["updated_at"] = _now()
        _save_jobs(data, jobs_path)
        return _public_job(job)


def _launch(job_id, context, *, jobs_path, tasks_dir, ledger_path, analyzer, route_runner, background, resume_thread_id=""):
    runner = threading.Thread(
        target=_run_job,
        kwargs={
            "job_id": job_id,
            "context": context,
            "jobs_path": jobs_path,
            "tasks_dir": tasks_dir,
            "ledger_path": ledger_path,
            "analyzer": analyzer,
            "route_runner": route_runner,
            "resume_thread_id": resume_thread_id,
        },
        daemon=True,
        name=f"codex-workbench-{job_id[:8]}",
    )
    with _LOCK:
        _RUNNING.add(job_id)
    if background:
        runner.start()
        return _public_job(_job(job_id, jobs_path))
    runner.run()
    return _public_job(_job(job_id, jobs_path))


def _run_job(job_id, context, jobs_path, tasks_dir, ledger_path, analyzer=None, route_runner=None, resume_thread_id=""):
    try:
        job = _update_job(job_id, jobs_path, status="analyzing", message="Codex 正在分析竞品和模板")
        task_dir = Path(tasks_dir) / safe_name(job_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        prompt = _analysis_prompt(context, task_dir, job.get("user_request", ""), continuing=bool(resume_thread_id))
        analyze = analyzer or _codex_analyze
        response = analyze(prompt, thread_id=resume_thread_id or None)
        if not isinstance(response, dict):
            raise ValueError("Codex 没有返回结构化分析结果。")
        thread_id = str(response.get("thread_id") or resume_thread_id or "")
        result = response.get("result") if isinstance(response.get("result"), dict) else response
        _update_job(
            job_id,
            jobs_path,
            thread_id=thread_id,
            last_response=json.dumps(result, ensure_ascii=False)[:MAX_RESPONSE],
        )
        if result.get("status") == "needs_input":
            _update_job(job_id, jobs_path, status="needs_input", message=str(result.get("message") or "需要补充商品资料。"))
            return
        task = _manifest_task(result.get("manifest_json"), context)
        _execute_core(
            job_id,
            job,
            task,
            jobs_path=jobs_path,
            tasks_dir=tasks_dir,
            ledger_path=ledger_path,
            route_runner=route_runner,
        )
    except Exception as exc:
        text = str(exc).strip() or exc.__class__.__name__
        if any(token in text.lower() for token in ("login", "auth", "account", "unauthorized")):
            text = "Codex 账号尚未在公司服务器完成授权。"
            status = "needs_setup"
        else:
            status = "failed"
        _update_job(job_id, jobs_path, status=status, message=text[:1000])
    finally:
        with _LOCK:
            _RUNNING.discard(job_id)


def _execute_core(job_id, job, task, *, jobs_path, tasks_dir, ledger_path, route_runner=None):
    task_dir = Path(tasks_dir) / safe_name(job_id)
    output_dir = task_dir / "outputs"
    task_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = task_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps({"output_dir": str(output_dir), "tasks": [task]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _update_job(job_id, jobs_path, status="generating", message="核心代码正在写表并执行自检")
    run_route = route_runner or run_batch_fast_prelisting
    core = run_route(manifest_path, output_dir=output_dir)
    item = (core.get("results") or [{}])[0]
    core_status = str(item.get("status") or "failed")
    output = Path(item["output"]).resolve() if item.get("output") else None
    fields = {}
    if output and output.is_file() and output.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        fields["output_file"] = str(output)
        fields["status"] = "待复核" if core_status == "ready_for_review" else "需修正"
        if task.get("estimated_price") not in {None, ""}:
            fields["note"] = "预估价格"
        update_row(job["batch_id"], job["row_id"], fields, ledger_path=ledger_path)
    if core_status == "ready_for_review" and output:
        status = "completed"
    elif core_status in {"needs_manual_fix", "needs_wps"}:
        status = "needs_input"
    else:
        status = "failed"
    try:
        record_fill_event(
            asin=str(job.get("row_id") or "").split("--", 1)[0],
            msku=task.get("parent_sku") or task.get("child_sku") or "",
            product_name=task.get("product_name") or task.get("name") or "",
            product_type=task.get("product_type") or "",
            template_path=task.get("template") or "",
            outcome=core_status,
            error_codes=item.get("error_codes") or [],
            evidence={"job_id": job_id, "message": item.get("message", ""), "output": str(output) if output else ""},
        )
    except Exception:
        pass
    return _update_job(
        job_id,
        jobs_path,
        status=status,
        core_status=core_status,
        output_file=str(output) if output else "",
        message=str(item.get("message") or "任务执行完成。"),
    )


def _codex_analyze(prompt, thread_id=None):
    from openai_codex import Codex, Sandbox

    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["ready", "needs_input"]},
            "message": {"type": "string"},
            "manifest_json": {"type": "string"},
        },
        "required": ["status", "message", "manifest_json"],
        "additionalProperties": False,
    }
    model = os.getenv("CODEX_WORKBENCH_MODEL", "").strip() or None
    with Codex() as codex:
        kwargs = {"cwd": str(ROOT), "sandbox": Sandbox.read_only}
        if model:
            kwargs["model"] = model
        thread = codex.thread_resume(thread_id, **kwargs) if thread_id else codex.thread_start(**kwargs)
        result = thread.run(prompt, output_schema=schema)
        parsed = json.loads(result.final_response)
        return {"thread_id": thread.id, "result": parsed}


def _analysis_prompt(context, task_dir, user_request, continuing=False):
    row = context["row"]
    files = row["resolved_files"]
    extra = user_request or "无额外要求"
    experience = lookup_experience(asin=row.get("asin") or row.get("id"), limit=6)
    experience_text = json.dumps(experience, ensure_ascii=False, indent=2) if experience else "没有检索到同 ASIN 历史记录。"
    action = "继续完善" if continuing else "建立"
    return f"""你正在为公司“上品工作台”{action}一个 Amazon 上品任务。

只做资料分析，不修改任何文件，不直接填写 Excel。最终返回符合输出 schema 的 JSON；manifest_json 字段中放一个 JSON 对象，它必须是可供项目 batch-fast-prelist 核心处理的单个 task 对象。

在分析前依次完整阅读：
1. {ROOT / 'PROJECT_RULES.md'}
2. {ROOT / 'docs' / 'amazon_template_fill_workflow.md'}
3. {ROOT / 'data' / 'reference_docs' / '亚马逊上传表格_通用自检资料.md'}
4. {ROOT / 'app' / 'template_writer.py'}
5. {ROOT / 'app' / 'template_validator.py'}
6. {ROOT / 'app' / 'success_rule_defaults.py'}
7. {ROOT / 'docs' / 'batch_fast_prelisting.md'}

任务信息：
- 商品/ASIN：{row.get('asin') or row.get('id')}
- 商品链接：{row.get('link') or ''}
- 竞品 HTML：{files.get('competitor_html')}
- Amazon 原始模板：{files.get('source_template')}
- 任务目录（仅供识别）：{task_dir}
- 用户补充要求：{extra}

上品经验池优先检索结果：
{experience_text}

经验池中的 needs_review/reference_only 只能作为线索，不得覆盖当前模板 Valid Values、项目规则或当前商品证据；validated/validated_reference 也必须再经过本次现有校验器。

manifest task 要遵守项目已有默认值，使用竞品当前商品信息和价格规则，不填写图片，不写竞品 ASIN 到新模板。必须给出 name、product_name，并尽可能给出价格、属性、variation_theme、variants 或物流信息。不要猜测敏感合规属性；确实缺少会改变结果的资料时返回 status=needs_input，并在 message 中用中文明确说明。资料足够时返回 status=ready。template、competitor/competitors 和输出目录由服务器强制注入，manifest_json 中即使包含也会被覆盖。
"""


def _manifest_task(raw, context):
    if not raw:
        raise ValueError("Codex 未生成任务清单。")
    task = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(task, dict):
        raise ValueError("Codex 生成的任务清单格式不正确。")
    row = context["row"]
    files = row["resolved_files"]
    clean = {str(key): value for key, value in task.items() if not str(key).startswith("_")}
    clean["name"] = str(clean.get("name") or row.get("asin") or row.get("id") or "上品任务")
    clean["product_name"] = str(clean.get("product_name") or clean["name"])
    clean["template"] = files["source_template"]
    clean["competitors"] = [files["competitor_html"]]
    clean.pop("competitor", None)
    clean.pop("output_dir", None)
    clean.pop("copy_reference", None)
    return clean


def _missing_inputs(row):
    files = row.get("resolved_files", {})
    missing = []
    competitor = Path(files.get("competitor_html") or "")
    template = Path(files.get("source_template") or "")
    if not competitor.is_file():
        missing.append("竞品 HTML")
    if not template.is_file():
        missing.append("Amazon 原始模板")
    return missing


def _find_job(data, job_id):
    job = next((item for item in data.get("jobs", []) if item.get("id") == job_id), None)
    if job is None:
        raise ValueError("找不到 Codex 任务。")
    return job


def _job(job_id, jobs_path):
    with _LOCK:
        return dict(_find_job(_load_jobs(jobs_path), job_id))


def _update_job(job_id, jobs_path, **fields):
    with _LOCK:
        data = _load_jobs(jobs_path)
        job = _find_job(data, job_id)
        for key, value in fields.items():
            if key in {
                "status",
                "execution_mode",
                "core_status",
                "message",
                "user_request",
                "thread_id",
                "worker_thread_id",
                "worker_thread_owner",
                "claimed_by",
                "claimed_at",
                "output_file",
                "last_response",
            }:
                job[key] = value
        job["updated_at"] = _now()
        _save_jobs(data, jobs_path)
        return _public_job(job)


def _public_job(job):
    public = {
        key: job.get(key, "")
        for key in (
            "id",
            "batch_id",
            "row_id",
            "status",
            "execution_mode",
            "core_status",
            "message",
            "claimed_by",
            "claimed_at",
            "output_file",
            "created_at",
            "updated_at",
        )
    }
    public["can_continue"] = bool(job.get("thread_id") or job.get("worker_thread_id")) and job.get("status") in {
        "needs_input",
        "failed",
        "needs_setup",
    }
    public["can_claim"] = job.get("execution_mode") == "manual_workers" and job.get("status") in {
        "waiting_claim",
        "needs_input",
        "failed",
    }
    return public


def _worker_id(value):
    worker_id = safe_name(str(value or "").strip())[:40]
    if not worker_id:
        raise ValueError("电脑名称不能为空。")
    return worker_id
