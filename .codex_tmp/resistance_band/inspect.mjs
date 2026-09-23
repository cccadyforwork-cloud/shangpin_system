import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "/Users/cc/Desktop/弹力带价格刷新.xlsx";
const outDir = "/Users/cc/Documents/GitHub/shangpin_system/.codex_tmp/resistance_band";
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

for (const query of ["LLD-TPE", "::record_action", "variation_theme", "parentage_level", "child_parent_sku_relationship", "Edit"]) {
  const result = await workbook.inspect({
    kind: "match",
    searchTerm: query,
    options: { useRegex: false, maxResults: 50 },
    maxChars: 12000,
  });
  console.log(`MATCH ${query}\n${result.ndjson}`);
}

const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 });
console.log(`SHEETS\n${sheets.ndjson}`);

const table = await workbook.inspect({ kind: "table", sheetId: "模板", range: "A1:J10", include: "values,formulas", tableMaxRows: 12, tableMaxCols: 12, maxChars: 16000 });
console.log(`TABLE\n${table.ndjson}`);
const dropdown = await workbook.inspect({ kind: "table", sheetId: "Dropdown Lists", range: "A1:F12", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8, maxChars: 12000 });
console.log(`DROPDOWN\n${dropdown.ndjson}`);
const preview = await workbook.render({ sheetName: "模板", range: "A1:J10", scale: 1.5, format: "png" });
await fs.writeFile(`${outDir}/before.png`, new Uint8Array(await preview.arrayBuffer()));
