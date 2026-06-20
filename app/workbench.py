import cgi
import json
import shutil
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .auto_fill import auto_fill_project
from .paths import DRAFT_DIRS, OUTPUTS_DIR, PROJECTS_DIR, PROJECT_FOLDERS, ROOT, TEMPLATE_DIRS, ensure_base_dirs, safe_name
from .project_manager import create_project, delete_project, list_project_summaries
from .project_status import infer_latest_template, infer_product_name, infer_sku_count, mark_uploaded_success
from .success_templates import RULES_JSON, RULES_REPORT, SUCCESS_TEMPLATES_DIR, learn_success_templates


STATUS_LABELS = {
    "uploaded_success": "已上传",
    "ready_for_upload": "待上传",
    "needs_manual_fix": "待修正",
    "blocked": "卡住",
    "not_started": "未开始",
}


def run_workbench(host="127.0.0.1", port=8765, open_browser=True):
    ensure_base_dirs()
    server = ThreadingHTTPServer((host, port), _handler())
    url = f"http://{host}:{port}"
    print(f"上品工作台已启动：{url}")
    print("按 Ctrl+C 停止。")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n工作台已停止。")
    finally:
        server.server_close()


def _handler():
    class WorkbenchHandler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/api/summary", "/api/rules", "/api/report"}:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8" if parsed.path == "/" else "application/json; charset=utf-8")
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_html(_html())
            elif parsed.path == "/api/summary":
                self._send_json(_summary_payload())
            elif parsed.path == "/api/rules":
                self._send_json(_rules_payload())
            elif parsed.path == "/api/report":
                self._send_json(_report_payload())
            else:
                self._send_json({"error": "not_found"}, status=404)

        def do_POST(self):
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/api/upload-files":
                    result = self._handle_file_upload()
                else:
                    payload = self._read_json()
                    if parsed.path == "/api/projects":
                        result = _create_project(payload)
                    elif parsed.path == "/api/auto-fill":
                        result = _auto_fill(payload)
                    elif parsed.path == "/api/mark-uploaded":
                        result = _mark_uploaded(payload)
                    elif parsed.path == "/api/delete-project":
                        result = _delete_project(payload)
                    elif parsed.path == "/api/learn-success":
                        result = _learn_success()
                    else:
                        self._send_json({"error": "not_found"}, status=404)
                        return
                self._send_json(result)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)

        def _handle_file_upload(self):
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                raise ValueError("上传请求格式不正确。")
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                },
            )
            project_dir = form.getfirst("project_dir", "")
            folder = form.getfirst("folder", "")
            files = []
            if "files" in form:
                files_field = form["files"]
                files = files_field if isinstance(files_field, list) else [files_field]
            return _upload_files(project_dir, folder, files)

        def log_message(self, _format, *_args):
            return

        def _read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not length:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _send_html(self, text, status=200):
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, payload, status=200):
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return WorkbenchHandler


def _summary_payload():
    projects = []
    counts = {}
    for item in list_project_summaries():
        status = item["status"]
        counts[status] = counts.get(status, 0) + 1
        project_dir = item["project_dir"]
        projects.append({
            "folder": item["folder"],
            "product_name": item["product_name"],
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "sku_count": item["sku_count"] or "",
            "template_error_count": item["template_error_count"],
            "latest_template": item["latest_template"],
            "updated_at": item["updated_at"][:10] if item["updated_at"] else "",
            "blocked_reason": item["blocked_reason"],
            "project_dir": str(project_dir),
            "relative_dir": _relative(project_dir),
            "next_step": _next_step(item),
            "has_template": _has_template(project_dir),
            "has_draft": _has_draft(project_dir),
        })
    return {
        "root": str(ROOT),
        "projects_dir": str(PROJECTS_DIR),
        "outputs_dir": str(OUTPUTS_DIR),
        "success_templates_dir": str(SUCCESS_TEMPLATES_DIR),
        "project_folders": PROJECT_FOLDERS,
        "counts": counts,
        "projects": projects,
        "totals": {
            "projects": len(projects),
            "uploaded": counts.get("uploaded_success", 0),
            "ready": counts.get("ready_for_upload", 0),
            "needs_fix": counts.get("needs_manual_fix", 0),
            "blocked": counts.get("blocked", 0),
            "not_started": counts.get("not_started", 0),
        },
    }


def _upload_files(project_dir, folder, file_items):
    project_path = _project_path({"project_dir": project_dir})
    if project_path == PROJECTS_DIR.resolve():
        raise ValueError("请选择具体项目。")
    if folder not in PROJECT_FOLDERS:
        raise ValueError("资料夹不正确。")
    real_files = [item for item in file_items if getattr(item, "filename", "") and getattr(item, "file", None)]
    if not real_files:
        raise ValueError("请选择文件。")

    target_dir = project_path / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for item in real_files:
        filename = _safe_upload_filename(item.filename)
        output_path = _unique_file_path(target_dir, filename)
        item.file.seek(0)
        with output_path.open("wb") as output:
            shutil.copyfileobj(item.file, output)
        saved.append({
            "name": output_path.name,
            "path": str(output_path),
            "relative_path": _relative(output_path),
        })

    return {
        "ok": True,
        "message": f"已放入 {len(saved)} 个文件",
        "folder": folder,
        "files": saved,
    }


def _safe_upload_filename(filename):
    name = Path(str(filename).replace("\\", "/")).name
    cleaned = safe_name(name)
    if cleaned in {".", ".."}:
        cleaned = "uploaded_file"
    return cleaned


def _unique_file_path(folder, filename):
    path = folder / filename
    if not path.exists():
        return path
    original = Path(filename)
    stem = original.stem or "uploaded_file"
    suffix = original.suffix
    index = 2
    while True:
        candidate = folder / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1

def _rules_payload():
    if not RULES_JSON.exists():
        return {
            "exists": False,
            "template_count": 0,
            "product_type_count": 0,
            "product_types": [],
        }
    rules = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    product_types = []
    for product_type, data in sorted(rules.get("product_types", {}).items()):
        product_types.append({
            "product_type": product_type,
            "template_count": data.get("template_count", 0),
            "sku_count": data.get("sku_count", 0),
            "fixed_default_count": len(data.get("fixed_default_fields", [])),
            "unmapped_count": len(data.get("often_filled_unmapped_fields", [])),
        })
    return {
        "exists": True,
        "template_count": rules.get("template_count", 0),
        "product_type_count": rules.get("product_type_count", 0),
        "report_path": str(RULES_REPORT),
        "json_path": str(RULES_JSON),
        "product_types": product_types,
    }


def _report_payload():
    if not RULES_REPORT.exists():
        return {"exists": False, "preview": ""}
    lines = RULES_REPORT.read_text(encoding="utf-8").splitlines()
    return {
        "exists": True,
        "path": str(RULES_REPORT),
        "preview": "\n".join(lines[:80]),
    }


def _create_project(payload):
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("请填写产品名。")
    project_dir, intake_path = create_project(name)
    return {
        "ok": True,
        "message": "项目已创建",
        "project_dir": str(project_dir),
        "intake_path": str(intake_path),
    }


def _auto_fill(payload):
    project_dir = _project_path(payload)
    result = auto_fill_project(project_dir, force=bool(payload.get("force")))
    cleaned = {key: str(value) for key, value in result.items() if key.endswith("_path") or key.endswith("_dir")}
    return {
        "ok": True,
        "message": _auto_fill_message(result),
        "status": result.get("status"),
        "skipped": result.get("skipped", False),
        "blocked": result.get("blocked", False),
        "paths": cleaned,
        "sku_count": result.get("sku_count"),
        "error_count": result.get("error_count"),
    }


def _mark_uploaded(payload):
    project_dir = _project_path(payload)
    template_path = infer_latest_template(project_dir)
    if template_path is None:
        raise ValueError("没有找到可标记的上传模板。")
    product_name = infer_product_name(project_dir, "")
    sku_count = infer_sku_count(project_dir)
    status_path = mark_uploaded_success(
        project_dir,
        product_name=product_name,
        latest_template=template_path,
        sku_count=sku_count,
        notes="工作台标记上传成功",
    )
    return {
        "ok": True,
        "message": "已标记上传成功",
        "status_path": str(status_path),
    }


def _delete_project(payload):
    project_dir = _project_path(payload)
    deleted_path = delete_project(project_dir)
    return {
        "ok": True,
        "message": f"项目已删除：{deleted_path.name}",
        "project_dir": str(deleted_path),
    }


def _learn_success():
    rules, json_path, report_path = learn_success_templates()
    return {
        "ok": True,
        "message": "成功规则已更新",
        "template_count": rules["template_count"],
        "product_type_count": rules["product_type_count"],
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def _project_path(payload):
    value = str(payload.get("project_dir", "")).strip()
    if not value:
        raise ValueError("缺少项目路径。")
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    try:
        path.relative_to(PROJECTS_DIR.resolve())
    except ValueError as exc:
        raise ValueError("项目路径必须在 data/projects 下。") from exc
    if not path.exists():
        raise ValueError("项目不存在。")
    return path


def _auto_fill_message(result):
    if result.get("skipped"):
        return "项目已上传，已跳过"
    if result.get("blocked"):
        return f"自动填表暂停：{result.get('reason')}"
    if result.get("status") == "ready_for_upload":
        return "自动填表完成，可进入人工上传"
    return "自动填表完成，需要查看自检报告"


def _next_step(item):
    status = item["status"]
    if status == "uploaded_success":
        return "归档"
    if status == "ready_for_upload":
        return "上传 Amazon 后标记成功"
    if status == "needs_manual_fix":
        return "查看自检报告并修正"
    if status == "blocked":
        return item["blocked_reason"] or "补齐资料"
    return "放入资料并自动填表"


def _has_template(project_dir):
    for folder in TEMPLATE_DIRS:
        path = Path(project_dir) / folder
        if path.exists() and any(item.suffix.lower() in {".xlsx", ".xlsm"} for item in path.iterdir() if item.is_file()):
            return True
    return False


def _has_draft(project_dir):
    for folder in DRAFT_DIRS:
        path = Path(project_dir) / folder
        if path.exists() and any("自动提炼草稿" in item.name for item in path.iterdir() if item.is_file()):
            return True
    return False


def _relative(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def _html():
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>上品工作台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --panel-2: #f1f5f2;
      --text: #20231f;
      --muted: #667065;
      --line: #d9dfd8;
      --green: #287457;
      --blue: #245f8f;
      --red: #a34037;
      --yellow: #8a6a18;
      --shadow: 0 10px 28px rgba(36, 48, 39, .08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }
    .app { min-height: 100vh; display: grid; grid-template-columns: 232px 1fr; }
    aside {
      background: #26322b;
      color: #f7f7f4;
      padding: 22px 16px;
      position: sticky;
      top: 0;
      height: 100vh;
    }
    .brand { font-size: 20px; font-weight: 750; margin-bottom: 22px; }
    nav { display: grid; gap: 8px; }
    nav button {
      appearance: none;
      border: 0;
      background: transparent;
      color: #dfe8df;
      text-align: left;
      padding: 10px 12px;
      border-radius: 8px;
      font: inherit;
      cursor: pointer;
    }
    nav button.active, nav button:hover { background: rgba(255,255,255,.12); color: #fff; }
    main { padding: 24px; min-width: 0; }
    .topbar { display: flex; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 18px; }
    h1 { font-size: 24px; margin: 0; letter-spacing: 0; }
    h2 { font-size: 17px; margin: 0 0 12px; letter-spacing: 0; }
    .muted { color: var(--muted); }
    .grid { display: grid; gap: 14px; }
    .stats { grid-template-columns: repeat(5, minmax(120px, 1fr)); margin-bottom: 16px; }
    .stat, .panel, .project, .rule {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .stat { padding: 14px; min-height: 82px; }
    .stat .num { font-size: 26px; font-weight: 760; margin-top: 4px; }
    .panel { padding: 16px; margin-bottom: 16px; }
    .toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    input, select {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 10px;
      min-width: 240px;
      font: inherit;
      background: #fff;
    }
    input[type="file"] {
      height: auto;
      padding: 7px 10px;
      min-width: min(420px, 100%);
    }
    button.action {
      height: 36px;
      border: 1px solid #b8c4ba;
      background: #fff;
      border-radius: 8px;
      padding: 0 12px;
      font: inherit;
      cursor: pointer;
      color: var(--text);
    }
    button.action.primary { background: var(--green); color: #fff; border-color: var(--green); }
    button.action.danger { color: var(--red); border-color: #d8aca7; background: #fff7f6; }
    button.action:hover { filter: brightness(.98); }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { color: var(--muted); font-weight: 650; background: var(--panel-2); }
    td { word-break: break-word; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #f6f7f4;
      white-space: nowrap;
    }
    .uploaded_success { color: var(--green); border-color: #bad7ca; background: #edf8f1; }
    .ready_for_upload { color: var(--blue); border-color: #bdd4e5; background: #edf5fa; }
    .needs_manual_fix, .blocked { color: var(--red); border-color: #e4c0bc; background: #fff0ee; }
    .not_started { color: var(--yellow); border-color: #ded1a8; background: #fbf6df; }
    .row-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .upload-panel .toolbar { align-items: flex-end; }
    .field { display: grid; gap: 5px; }
    .field label { color: var(--muted); font-size: 12px; }
    .upload-status { min-height: 18px; margin-top: 10px; }
    .selected-files {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfa;
      margin-top: 12px;
      min-height: 54px;
      max-height: 150px;
      overflow: auto;
      padding: 9px 10px;
    }
    .selected-files ul { margin: 0; padding-left: 18px; }
    .selected-files li { margin: 2px 0; }
    .small { font-size: 12px; }
    .rules-grid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
    .rule { padding: 12px; min-height: 118px; }
    .rule strong { display: block; margin-bottom: 8px; }
    pre {
      white-space: pre-wrap;
      background: #20231f;
      color: #eef4ee;
      padding: 14px;
      border-radius: 8px;
      max-height: 520px;
      overflow: auto;
      font-size: 12px;
    }
    .toast {
      position: fixed;
      right: 18px;
      bottom: 18px;
      max-width: 460px;
      background: #20231f;
      color: #fff;
      padding: 12px 14px;
      border-radius: 8px;
      box-shadow: 0 12px 32px rgba(0,0,0,.24);
      display: none;
    }
    .view { display: none; }
    .view.active { display: block; }
    @media (max-width: 920px) {
      .app { grid-template-columns: 1fr; }
      aside { height: auto; position: static; }
      nav { grid-template-columns: repeat(3, 1fr); }
      .stats { grid-template-columns: repeat(2, 1fr); }
      main { padding: 16px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand">上品工作台</div>
      <nav>
        <button data-view="projects" class="active">项目</button>
        <button data-view="rules">规则库</button>
        <button data-view="report">报告</button>
      </nav>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <h1 id="page-title">项目</h1>
          <div class="muted small" id="root-path"></div>
        </div>
        <button class="action" id="refresh-btn">刷新</button>
      </div>

      <section id="projects" class="view active">
        <div class="grid stats">
          <div class="stat"><div class="muted">全部项目</div><div class="num" id="stat-projects">0</div></div>
          <div class="stat"><div class="muted">已上传</div><div class="num" id="stat-uploaded">0</div></div>
          <div class="stat"><div class="muted">待上传</div><div class="num" id="stat-ready">0</div></div>
          <div class="stat"><div class="muted">待修正</div><div class="num" id="stat-fix">0</div></div>
          <div class="stat"><div class="muted">未开始</div><div class="num" id="stat-new">0</div></div>
        </div>
        <div class="panel">
          <h2>新建项目</h2>
          <div class="toolbar">
            <input id="new-project-name" placeholder="产品名">
            <button class="action primary" id="create-project-btn">新建</button>
          </div>
        </div>
        <div class="panel upload-panel" id="upload-panel">
          <h2>放资料</h2>
          <div class="toolbar">
            <div class="field">
              <label for="upload-project">项目</label>
              <select id="upload-project"></select>
            </div>
            <div class="field">
              <label for="upload-folder">资料夹</label>
              <select id="upload-folder"></select>
            </div>
            <div class="field">
              <label for="upload-files">文件</label>
              <input id="upload-files" type="file" multiple>
            </div>
            <button class="action primary" id="upload-files-btn">放入项目</button>
          </div>
          <div class="selected-files small" id="selected-files">未选择文件</div>
          <div class="muted small upload-status" id="upload-status"></div>
        </div>
        <div class="panel">
          <h2>项目状态</h2>
          <table>
            <thead>
              <tr>
                <th style="width: 18%">项目</th>
                <th style="width: 10%">状态</th>
                <th style="width: 8%">SKU</th>
                <th style="width: 24%">最新模板</th>
                <th style="width: 18%">下一步</th>
                <th style="width: 22%">操作</th>
              </tr>
            </thead>
            <tbody id="project-rows"></tbody>
          </table>
        </div>
      </section>

      <section id="rules" class="view">
        <div class="panel">
          <h2>成功规则</h2>
          <div class="toolbar">
            <button class="action primary" id="learn-success-btn">更新规则</button>
            <span class="muted small" id="rules-meta"></span>
          </div>
        </div>
        <div class="grid rules-grid" id="rules-grid"></div>
      </section>

      <section id="report" class="view">
        <div class="panel">
          <h2>成功模板规则提炼报告</h2>
          <div class="muted small" id="report-path"></div>
          <pre id="report-preview"></pre>
        </div>
      </section>
    </main>
  </div>
  <div class="toast" id="toast"></div>
  <script>
    const state = { summary: null, rules: null };

    function showToast(message) {
      const box = document.getElementById('toast');
      box.textContent = message;
      box.style.display = 'block';
      clearTimeout(showToast.timer);
      showToast.timer = setTimeout(() => box.style.display = 'none', 4200);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { 'Content-Type': 'application/json' },
        ...options
      });
      const data = await response.json();
      if (!response.ok || data.ok === false) throw new Error(data.error || '请求失败');
      return data;
    }

    async function loadAll() {
      const [summary, rules, report] = await Promise.all([
        api('/api/summary'),
        api('/api/rules'),
        api('/api/report'),
      ]);
      state.summary = summary;
      state.rules = rules;
      renderSummary(summary);
      renderRules(rules);
      renderReport(report);
    }

    function renderSummary(summary) {
      document.getElementById('root-path').textContent = summary.root;
      document.getElementById('stat-projects').textContent = summary.totals.projects;
      document.getElementById('stat-uploaded').textContent = summary.totals.uploaded;
      document.getElementById('stat-ready').textContent = summary.totals.ready;
      document.getElementById('stat-fix').textContent = summary.totals.needs_fix + summary.totals.blocked;
      document.getElementById('stat-new').textContent = summary.totals.not_started;

      const rows = document.getElementById('project-rows');
      rows.innerHTML = '';
      for (const project of summary.projects) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${escapeHtml(project.product_name)}</strong><div class="muted small">${escapeHtml(project.folder)}</div></td>
          <td><span class="badge ${project.status}">${escapeHtml(project.status_label)}</span></td>
          <td>${escapeHtml(project.sku_count || '-')}</td>
          <td><span class="small">${escapeHtml(project.latest_template || '-')}</span></td>
          <td>${escapeHtml(project.next_step || '-')}</td>
          <td><div class="row-actions">
            <button class="action" data-action="pick-upload" data-project="${escapeAttr(project.project_dir)}">放资料</button>
            <button class="action" data-action="auto-fill" data-project="${escapeAttr(project.project_dir)}">自动填表</button>
            <button class="action" data-action="mark-uploaded" data-project="${escapeAttr(project.project_dir)}">标记成功</button>
            <button class="action danger" data-action="delete-project" data-project="${escapeAttr(project.project_dir)}" data-name="${escapeAttr(project.product_name)}">删除</button>
          </div></td>
        `;
        rows.appendChild(tr);
      }
      renderUploadOptions(summary);
    }

    function renderUploadOptions(summary) {
      const projectSelect = document.getElementById('upload-project');
      const selectedProject = projectSelect.value;
      projectSelect.innerHTML = '';
      for (const project of summary.projects) {
        const option = document.createElement('option');
        option.value = project.project_dir;
        option.textContent = `${project.product_name} / ${project.folder}`;
        projectSelect.appendChild(option);
      }
      if ([...projectSelect.options].some(option => option.value === selectedProject)) {
        projectSelect.value = selectedProject;
      }

      const folderSelect = document.getElementById('upload-folder');
      const selectedFolder = folderSelect.value;
      folderSelect.innerHTML = '';
      for (const folder of summary.project_folders || []) {
        const option = document.createElement('option');
        option.value = folder;
        option.textContent = folder;
        folderSelect.appendChild(option);
      }
      if ([...folderSelect.options].some(option => option.value === selectedFolder)) {
        folderSelect.value = selectedFolder;
      }
    }

    function renderRules(rules) {
      document.getElementById('rules-meta').textContent = rules.exists
        ? `${rules.template_count} 个样板，${rules.product_type_count} 个 Product Type`
        : '暂无规则';
      const grid = document.getElementById('rules-grid');
      grid.innerHTML = '';
      for (const item of rules.product_types || []) {
        const div = document.createElement('div');
        div.className = 'rule';
        div.innerHTML = `
          <strong>${escapeHtml(item.product_type)}</strong>
          <div>样板：${item.template_count}</div>
          <div>SKU：${item.sku_count}</div>
          <div>固定默认值：${item.fixed_default_count}</div>
          <div>未映射常填字段：${item.unmapped_count}</div>
        `;
        grid.appendChild(div);
      }
    }

    function renderReport(report) {
      document.getElementById('report-path').textContent = report.path || '';
      document.getElementById('report-preview').textContent = report.preview || '暂无报告';
    }

    async function postAction(path, payload) {
      const result = await api(path, { method: 'POST', body: JSON.stringify(payload || {}) });
      showToast(result.message || '已完成');
      await loadAll();
    }

    document.addEventListener('click', async (event) => {
      const nav = event.target.closest('nav button');
      if (nav) {
        document.querySelectorAll('nav button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
        nav.classList.add('active');
        document.getElementById(nav.dataset.view).classList.add('active');
        document.getElementById('page-title').textContent = nav.textContent;
        return;
      }
      const action = event.target.dataset.action;
      if (action === 'pick-upload') {
        document.getElementById('upload-project').value = event.target.dataset.project;
        document.getElementById('upload-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      if (action === 'auto-fill') {
        await guarded(() => postAction('/api/auto-fill', { project_dir: event.target.dataset.project }));
      }
      if (action === 'mark-uploaded') {
        await guarded(() => postAction('/api/mark-uploaded', { project_dir: event.target.dataset.project }));
      }
      if (action === 'delete-project') {
        const name = event.target.dataset.name || '这个项目';
        if (window.confirm(`确定删除「${name}」吗？此操作会删除整个项目文件夹，不能从工作台恢复。`)) {
          await guarded(() => postAction('/api/delete-project', { project_dir: event.target.dataset.project }));
        }
      }
    });

    document.getElementById('refresh-btn').addEventListener('click', () => guarded(loadAll));
    document.getElementById('learn-success-btn').addEventListener('click', () => guarded(() => postAction('/api/learn-success')));
    document.getElementById('upload-files-btn').addEventListener('click', () => guarded(uploadFiles));
    document.getElementById('upload-files').addEventListener('change', renderSelectedFiles);
    document.getElementById('create-project-btn').addEventListener('click', async () => {
      const input = document.getElementById('new-project-name');
      await guarded(() => postAction('/api/projects', { name: input.value }));
      input.value = '';
    });

    async function uploadFiles() {
      const status = document.getElementById('upload-status');
      const fileInput = document.getElementById('upload-files');
      const projectDir = document.getElementById('upload-project').value;
      const folder = document.getElementById('upload-folder').value;
      if (!projectDir) throw new Error('请选择项目。');
      if (!folder) throw new Error('请选择资料夹。');
      if (!fileInput.files.length) throw new Error('请选择文件。');

      const form = new FormData();
      form.append('project_dir', projectDir);
      form.append('folder', folder);
      for (const file of fileInput.files) {
        form.append('files', file, file.name);
      }
      status.textContent = `正在放入 ${fileInput.files.length} 个文件...`;
      const response = await fetch('/api/upload-files', { method: 'POST', body: form });
      const result = await response.json();
      if (!response.ok || result.ok === false) throw new Error(result.error || '上传失败');
      fileInput.value = '';
      renderSelectedFiles();
      status.textContent = (result.files || []).map(file => file.relative_path).join('；');
      showToast(result.message || '文件已放入项目');
      await loadAll();
    }

    function renderSelectedFiles() {
      const fileInput = document.getElementById('upload-files');
      const box = document.getElementById('selected-files');
      const files = [...fileInput.files];
      if (!files.length) {
        box.textContent = '未选择文件';
        return;
      }
      const totalBytes = files.reduce((sum, file) => sum + file.size, 0);
      const items = files
        .map(file => `<li>${escapeHtml(file.name)} <span class="muted">(${formatBytes(file.size)})</span></li>`)
        .join('');
      box.innerHTML = `<div>${files.length} 个文件，合计 ${formatBytes(totalBytes)}</div><ul>${items}</ul>`;
    }

    function formatBytes(bytes) {
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    }

    async function guarded(fn) {
      try { await fn(); } catch (error) { showToast(error.message); }
    }

    function escapeHtml(value) {
      return String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[char]));
    }

    function escapeAttr(value) { return escapeHtml(value); }

    guarded(loadAll);
  </script>
</body>
</html>"""
