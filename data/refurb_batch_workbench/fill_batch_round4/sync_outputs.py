from pathlib import Path

from app.refurb_batch_workbench import BATCH_ID, LEDGER_PATH, attach_file, load_ledger, update_row


ROUND_DIR = Path(__file__).resolve().parent
OUTPUTS = ROUND_DIR / "outputs"
FILES = {
    "ROW-13": "冰袖4件装V1.xlsm",
    "ROW-16": "调料瓶蓝色2件装V1.xlsm",
    "B0GXYZZVLG": "清洁果蔬白灰色4件装V1.xlsm",
}


ledger = load_ledger(LEDGER_PATH)
rows = {
    row["id"]: row
    for batch in ledger.get("batches", [])
    if batch.get("id") == BATCH_ID
    for row in batch.get("rows", [])
}

for row_id, filename in FILES.items():
    source = OUTPUTS / filename
    if Path(str(rows[row_id].get("output_file") or "")).name != filename:
        with source.open("rb") as stream:
            attach_file(BATCH_ID, row_id, "output_file", filename, stream)
    note = str(rows[row_id].get("note") or "").strip()
    note_parts = [part for part in note.split("；") if part and part != "预估价格"]
    note_parts.append("预估价格")
    update_row(BATCH_ID, row_id, {"status": "可上传", "note": "；".join(note_parts)})
    print(row_id, filename)
