import fs from "node:fs/promises";
import path from "node:path";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "/private/tmp/huhtamaki_corp_workbook/all_corporates_filtered.json";
const outputDir = "/Users/l.paunikar/Desktop/nuetra-backend/outputs/corporate_workbooks";

const colName = (index) => {
  let n = index + 1;
  let name = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    name = String.fromCharCode(65 + rem) + name;
    n = Math.floor((n - 1) / 26);
  }
  return name;
};

const raw = await fs.readFile(inputPath, "utf8");
const corporates = JSON.parse(raw);

await fs.mkdir(outputDir, { recursive: true });

for (const [corporateName, sheets] of Object.entries(corporates)) {
  const workbook = Workbook.create();

  for (const [sheetName, sheetData] of Object.entries(sheets)) {
    const sheet = workbook.worksheets.add(sheetName);
    const rows = [sheetData.header, ...sheetData.rows];
    const width = sheetData.header.length || 1;
    const height = Math.max(rows.length, 1);
    const range = `A1:${colName(width - 1)}${height}`;
    sheet.getRange(range).values = rows.length ? rows : [[""]];
  }

  const filePath = path.join(outputDir, `${corporateName}.xlsx`);
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(filePath);
  console.log(filePath);
}
