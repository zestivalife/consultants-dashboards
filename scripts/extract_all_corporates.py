import json
from collections import OrderedDict

import pandas as pd

SOURCE_PATH = "/Users/l.paunikar/Downloads/MIS 23 to 31 May 26 - Mangala - R S.xls"
OUTPUT_PATH = "/private/tmp/huhtamaki_corp_workbook/all_corporates_filtered.json"

SHEETS = OrderedDict(
    [
        ("DOMESTIC DEBIT", 30),
        ("AIR CN", 24),
        ("INTERNATIONAL DEBIT", 27),
        ("RAIL DEBIT", 17),
        ("BUS DEBIT", 15),
        ("HOTEL DEBIT", 25),
        ("INTERNATIONAL CREDIT", 22),
        ("RAIL CREDIT", 18),
        ("HOTEL CREDIT", 21),
    ]
)


def normalize(value):
    if pd.isna(value):
        return ""
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()
    return str(value)


def main():
    xl = pd.ExcelFile(SOURCE_PATH)
    corp_order = OrderedDict()
    sheet_cache = OrderedDict()

    for sheet_name, corp_col in SHEETS.items():
        df = xl.parse(sheet_name, header=None, dtype=object)
        header = [normalize(v) for v in df.iloc[0].tolist()]
        body = df.iloc[1:].copy()
        body = body.fillna("")
        body["_corp"] = body[corp_col].astype(str).str.strip()
        sheet_cache[sheet_name] = {"header": header, "body": body}
        for corp in body["_corp"].tolist():
            if corp and corp.lower() != "total":
                corp_order.setdefault(corp, None)

    result = OrderedDict()
    for corp in corp_order.keys():
        result[corp] = OrderedDict()
        for sheet_name in SHEETS.keys():
            cached = sheet_cache[sheet_name]
            body = cached["body"]
            filtered = body[body["_corp"] == corp].drop(columns=["_corp"])
            rows = [[normalize(v) for v in row] for row in filtered.values.tolist()]
            result[corp][sheet_name] = {
                "header": cached["header"],
                "rows": rows,
                "count": len(rows),
            }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False)

    print(f"corporates={len(result)}")
    for corp, sheets in result.items():
        total_rows = sum(info["count"] for info in sheets.values())
        print(f"{corp}\t{total_rows}")


if __name__ == "__main__":
    main()
