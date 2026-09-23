import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "/Users/cc/Desktop/弹力带价格刷新.xlsx";
const outputDir = "/Users/cc/Documents/GitHub/shangpin_system/outputs/01a09a0d-5e1d-7473-8611-f221c4c977bf";
const outputPath = `${outputDir}/弹力带价格刷新V1.xlsx`;

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("模板");

// Shift the three existing child records down one row, bottom-up.
sheet.getRange("A10:IF10").copyFrom(sheet.getRange("A9:IF9"), "all");
sheet.getRange("A9:IF9").copyFrom(sheet.getRange("A8:IF8"), "all");
sheet.getRange("A8:IF8").copyFrom(sheet.getRange("A7:IF7"), "all");

// Convert row 7 into the backend parent record and keep parent-only fields lean.
sheet.getRange("A7:IF7").clear({ applyTo: "contents" });
sheet.getRange("A7:I7").values = [[
  "CA-LLD-Single",
  "EXERCISE_BAND",
  "Edit (Partial Update)",
  "Parent",
  null,
  "COLOR",
  "TPE Resistance Bands Flat Exercise Stretch Bands for Yoga Pilates Home Fitness Training",
  "Generic",
  "運動和戶外活動 > 運動與健身設備 > 力量訓練器材 > 彈力帶 (exercise-resistance-bands)",
]];

// Link every child to the parent and use the template's exact edit action enum.
sheet.getRange("C8:F10").values = [
  ["Edit (Partial Update)", "Child", "CA-LLD-Single", "COLOR"],
  ["Edit (Partial Update)", "Child", "CA-LLD-Single", "COLOR"],
  ["Edit (Partial Update)", "Child", "CA-LLD-Single", "COLOR"],
];

workbook.recalculate();

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

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
  maxChars: 12000,
});
console.log(`ERRORS\n${errors.ndjson}`);

const preview = await workbook.render({ sheetName: "模板", range: "A2:J10", scale: 1.5, format: "png" });
await fs.writeFile("/Users/cc/Documents/GitHub/shangpin_system/.codex_tmp/resistance_band/after.png", new Uint8Array(await preview.arrayBuffer()));

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`OUTPUT ${outputPath}`);
