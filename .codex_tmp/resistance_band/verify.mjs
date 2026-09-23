import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const finalPath = "/Users/cc/Documents/GitHub/shangpin_system/outputs/01a09a0d-5e1d-7473-8611-f221c4c977bf/弹力带价格刷新V3.xlsx";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(finalPath));
const check = await workbook.inspect({
  kind: "table",
  sheetId: "模板",
  range: "A4:J10",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 12,
  maxChars: 16000,
});
console.log(`CHECK\n${check.ndjson}`);
const copyCheck = await workbook.inspect({
  kind: "table",
  sheetId: "模板",
  range: "AB4:AG10",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 8,
  maxChars: 24000,
});
console.log(`COPY\n${copyCheck.ndjson}`);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
  maxChars: 12000,
});
console.log(`ERRORS\n${errors.ndjson}`);
for (const range of ["CZ4:DC10", "EA4:EC10"]) {
  const priceCheck = await workbook.inspect({
    kind: "table",
    sheetId: "模板",
    range,
    include: "values,formulas",
    tableMaxRows: 10,
    tableMaxCols: 8,
    maxChars: 12000,
  });
  console.log(`PRICE ${range}\n${priceCheck.ndjson}`);
}
const preview = await workbook.render({ sheetName: "模板", range: "EA3:EC10", scale: 1.5, format: "png" });
await fs.writeFile("/Users/cc/Documents/GitHub/shangpin_system/.codex_tmp/resistance_band/final_v3.png", new Uint8Array(await preview.arrayBuffer()));
