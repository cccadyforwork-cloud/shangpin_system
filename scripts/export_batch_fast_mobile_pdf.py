#!/usr/bin/env python3
import argparse
import html
import subprocess
import tempfile
from pathlib import Path

from app.batch_fast_workbench import load_ledger


CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def text(value):
    return html.escape(str(value or "—"))


def file_name(row, field):
    value = str(row.get(field) or "").strip()
    return Path(value).name if value else "—"


def render(batch_id, store_id):
    ledger = load_ledger()
    batch = next(item for item in ledger["batches"] if item["id"] == batch_id)
    rows = sorted(
        (row for row in batch["rows"] if row.get("store_id") == store_id),
        key=lambda row: row.get("row_number") or 0,
    )
    stats = {
        "已上传": sum(row.get("status") == "已上传" for row in rows),
        "可上传": sum(row.get("status") == "可上传" for row in rows),
        "已采购": sum(row.get("purchase_status") == "已采购" for row in rows),
        "预估价格": sum(row.get("note") == "预估价格" for row in rows),
    }
    cards = []
    for index, row in enumerate(rows, 1):
        status = str(row.get("status") or "—")
        purchase = str(row.get("purchase_status") or "—")
        status_class = " green" if status in {"已上传", "可上传"} else ""
        purchase_class = " green" if purchase == "已采购" else ""
        note_class = " note" if row.get("note") else ""
        link = html.escape(str(row.get("link") or "#"), quote=True)
        cards.append(f"""
        <section class="card">
          <div class="cardtop">
            <span class="num">{index}</span><span class="asin">{text(row.get('asin') or row.get('id'))}</span>
            <div class="badges"><span class="badge{status_class}">{text(status)}</span><span class="badge{purchase_class}">{text(purchase)}</span></div>
          </div>
          <div class="grid">
            <span class="label">商品链接</span><span><a href="{link}">打开 Amazon 商品页</a></span>
            <span class="label">竞品 HTML</span><span class="file">{text(file_name(row, 'competitor_html'))}</span>
            <span class="label">原始模板</span><span class="file">{text(file_name(row, 'source_template'))}</span>
            <span class="label">当前输出</span><span class="file">{text(file_name(row, 'output_file'))}</span>
            <span class="label">备注</span><span class="{note_class}">{text(row.get('note'))}</span>
          </div>
        </section>""")
    stat_html = "".join(f'<div class="stat"><b>{value}</b>{label}</div>' for label, value in stats.items())
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{text(batch['name'])} {text(store_id)}</title>
<style>
@page {{ size: A4 portrait; margin: 10mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", Arial, sans-serif; color: #172033; background: #fff; font-size: 10.5pt; }}
.head {{ border-bottom: 2px solid #172033; padding-bottom: 8px; margin-bottom: 10px; }}
.title {{ font-size: 21pt; font-weight: 800; }}
.sub {{ margin-top: 4px; color: #5b6475; }}
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 9px; }}
.stat {{ background: #f3f6fa; border: 1px solid #dce2ea; border-radius: 6px; padding: 6px; text-align: center; }}
.stat b {{ display: block; font-size: 14pt; }}
.card {{ border: 1px solid #aeb8c6; border-radius: 7px; margin: 0 0 7px; padding: 8px 9px; break-inside: avoid; page-break-inside: avoid; }}
.cardtop {{ display: flex; align-items: center; gap: 7px; margin-bottom: 6px; }}
.num {{ min-width: 25px; height: 25px; border-radius: 50%; display: grid; place-items: center; background: #172033; color: #fff; font-weight: 700; }}
.asin {{ font-size: 12pt; font-weight: 800; }}
.badges {{ margin-left: auto; display: flex; gap: 4px; }}
.badge {{ border-radius: 10px; padding: 2px 7px; font-size: 8.5pt; border: 1px solid #b8c2d0; background: #eef2f7; }}
.green {{ background: #dff5e6; border-color: #7bc48f; color: #17662f; }}
.grid {{ display: grid; grid-template-columns: 72px 1fr; column-gap: 7px; row-gap: 3px; }}
.label {{ color: #687286; }}
.file {{ color: #25344d; overflow-wrap: anywhere; }}
.note {{ color: #9a5d00; font-weight: 700; }}
a {{ color: #1260a8; text-decoration: none; }}
.footer {{ margin-top: 7px; color: #7a8493; text-align: center; font-size: 8.5pt; }}
</style></head><body>
<header class="head"><div class="title">{text(batch['name'])} · {text(store_id)}工作台</div><div class="sub">手机查看版 · 2026-09-05 · 共 {len(rows)} 个商品</div><div class="stats">{stat_html}</div></header>
<main>{''.join(cards)}</main><div class="footer">数据来源：快速上品工作台 {text(batch['name'])} {text(store_id)}</div>
</body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", default="cady选品")
    parser.add_argument("--store", default="2店")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if not CHROME.exists():
        raise FileNotFoundError(CHROME)
    with tempfile.TemporaryDirectory(prefix="batch_fast_pdf_") as temp_dir:
        html_path = Path(temp_dir) / "workbench.html"
        html_path.write_text(render(args.batch, args.store), encoding="utf-8")
        subprocess.run([
            str(CHROME), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
            f"--user-data-dir={Path(temp_dir) / 'chrome'}", f"--print-to-pdf={output}", html_path.as_uri(),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(output)


if __name__ == "__main__":
    main()
