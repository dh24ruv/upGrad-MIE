import os
import requests
from dotenv import load_dotenv

load_dotenv()

INSTA_API_KEY = os.getenv("INSTA_API_KEY")
BASE = "https://www.instafinancials.com"
HEADERS = {"user-key": INSTA_API_KEY}

def get_cin(company_name: str) -> str | None:
    # "nc" mode = contains, "sw" = starts with
    url = f"{BASE}/GetCIN/v1/json/Search/{company_name}/Mode/nc"
    r = requests.get(url, headers=HEADERS)
    print(f"CIN response: {r.status_code} → {r.text[:800]}")
    if r.status_code != 200:
        return None
    data = r.json()
    # Returns a list — grab the first match
    companies = data.get("data", data.get("Data", []))
    if companies:
        first = companies[0]
        cin = first.get("CIN") or first.get("cin")
        print(f"Best match: {first.get('companyName') or first.get('CompanyName')} → {cin}")
        return cin
    return None

def get_private_financials(company_name: str) -> dict:
    cin = get_cin(company_name)
    if not cin:
        print("No CIN found — stopping.")
        return {}
    print(f"\nFetching financials for CIN: {cin}")
    url = f"{BASE}/InstaSummary/v1/json/{cin}"
    r = requests.get(url, headers=HEADERS)
    print(f"Financials response: {r.status_code} → {r.text[:1500]}")
    if r.status_code != 200:
        return {}
    return r.json()

if __name__ == "__main__":
    result = get_private_financials("Unacademy")
    print("\nFinal result:")
    print(result)