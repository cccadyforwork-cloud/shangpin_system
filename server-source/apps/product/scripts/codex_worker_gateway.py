#!/usr/bin/env python3
"""Restricted SSH gateway used by trusted manual Codex workers."""

import argparse
import base64
import json
import os
import shlex
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.codex_workbench import (  # noqa: E402
    claim_manual_job,
    fail_manual_job,
    manual_job_file,
    release_manual_job,
    submit_manual_analysis,
)


def _json(value):
    sys.stdout.write(json.dumps(value, ensure_ascii=False))
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-id", required=True)
    args = parser.parse_args()
    command = shlex.split(os.environ.get("SSH_ORIGINAL_COMMAND", ""))
    if not command:
        raise ValueError("缺少 Worker 命令。")
    action = command[0]
    if action == "health" and len(command) == 1:
        _json({"ok": True, "worker_id": args.worker_id})
        return
    if len(command) != 2:
        raise ValueError("Worker 命令格式不正确。")
    job_id = command[1]
    if action == "claim":
        _json(claim_manual_job(job_id, args.worker_id))
    elif action in {"fetch-competitor", "fetch-template"}:
        field = "competitor_html" if action == "fetch-competitor" else "source_template"
        path = manual_job_file(job_id, args.worker_id, field)
        _json(
            {
                "ok": True,
                "name": path.name,
                "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
        )
    elif action == "submit":
        payload = json.load(sys.stdin)
        _json(submit_manual_analysis(job_id, args.worker_id, payload))
    elif action == "fail":
        payload = json.load(sys.stdin)
        _json(fail_manual_job(job_id, args.worker_id, payload.get("message", "")))
    elif action == "release":
        _json(release_manual_job(job_id, args.worker_id))
    else:
        raise ValueError("不支持的 Worker 命令。")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _json({"ok": False, "error": str(exc)[:1000]})
        raise SystemExit(1)
