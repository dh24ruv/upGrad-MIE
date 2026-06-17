import requests
import csv
import io
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/Users/dhruvpande/upgrad/.env")

# ---- CONFIG ----
SHEET_ID = "13Zt9TbG4eXaZn6ZzSnVcZuAm7Gw9jB9Ucsz5Dhovxeg"   # paste your sheet ID
SHEET_NAME = "Financials of Education Company - Master"              # change if your tab is named differently

# ---- CLIENTS ----
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_sheet_data(sheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch sheet: {response.status_code}")
    reader = csv.reader(io.StringIO(response.text))
    return list(reader)

def safe_float(val):
    try:
        if val in [None, "", "N/A", "-", "—"]:
            return None
        return float(str(val).replace(",", "").replace("₹", "").strip())
    except:
        return None

def safe_str(val):
    if val in [None, "", "N/A", "-", "—"]:
        return None
    return str(val).strip()

def extract_and_load():
    print("Fetching sheet data...")
    all_rows = get_sheet_data(SHEET_ID, SHEET_NAME)

    print(f"Total rows fetched: {len(all_rows)}")

    # Row 0 = first header, Row 1 = sub-header, data starts Row 2
    data_rows = all_rows[2:]

    inserted = 0
    skipped = 0

    for row in data_rows:
        # Skip empty rows
        if not row or not safe_str(row[1] if len(row) > 1 else ""):
            skipped += 1
            continue

        def get(index):
            try:
                return row[index]
            except IndexError:
                return None

        company = {
            "name":                 safe_str(get(1)),
            "legal_name":           safe_str(get(1)),
            "notes":                safe_str(get(7)),

            # FY25
            "revenue_fy25":         safe_float(get(8)),
            "ebitda_fy25":          safe_float(get(9)),
            "net_income_fy25":      safe_float(get(10)),

            # FY24
            "revenue_fy24":         safe_float(get(11)),
            "ebitda_fy24":          safe_float(get(12)),
            "net_loss_fy24":        safe_float(get(13)),

            # FY23
            "revenue_fy23":         safe_float(get(14)),
            "ebitda_fy23":          safe_float(get(15)),
            "net_loss_fy23":        safe_float(get(16)),

            "financial_source":     "MCA filing",
            "confidence_financial": "High",
        }

        if not company["name"]:
            skipped += 1
            continue

        result = supabase.table("companies") \
            .upsert(company, on_conflict="name") \
            .execute()

        inserted += 1
        print(f"✓ {company['name']}")

    print(f"\nDone. {inserted} companies loaded, {skipped} rows skipped.")

if __name__ == "__main__":
    extract_and_load()