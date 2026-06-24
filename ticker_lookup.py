"""
Dynamic NSE ticker lookup — replaces the hardcoded ticker_map in app.py.

Downloads NSE's official equity list once (cached locally, refreshed every
N days), then fuzzy-matches a company name against it to find the right
.NS ticker for yfinance. No more manually adding new IPOs (e.g. PWL) by hand.
"""

import os
import re
import json
import time
import difflib
import requests

NSE_EQUITY_LIST_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
CACHE_PATH = "/Users/dhruvpande/upgrad/.nse_equity_cache.json"
CACHE_MAX_AGE_DAYS = 7  # refresh weekly — frequent enough to catch new IPOs

# Common corporate suffixes/noise words to strip before matching, so
# "Naukri" matches "Info Edge (India) Limited" style names better and
# "Unacademy Pvt Ltd" doesn't fail to match purely on "Limited" noise.
_SUFFIX_WORDS = {
    "limited", "ltd", "ltd.", "private", "pvt", "pvt.", "inc", "inc.",
    "company", "co", "co.", "corporation", "corp", "the", "india", "(india)",
}

def _normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)  # strip punctuation
    tokens = [t for t in name.split() if t not in _SUFFIX_WORDS]
    return " ".join(tokens).strip()


def _download_equity_list() -> list[dict]:
    """Fetch NSE's official equity list. Returns list of {symbol, name}."""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(NSE_EQUITY_LIST_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    lines = resp.text.strip().split("\n")
    header = [h.strip().upper() for h in lines[0].split(",")]
    sym_idx = header.index("SYMBOL")
    name_idx = header.index("NAME OF COMPANY")

    rows = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) <= max(sym_idx, name_idx):
            continue
        symbol = parts[sym_idx].strip()
        company = parts[name_idx].strip()
        if symbol and company:
            rows.append({"symbol": symbol, "name": company, "norm": _normalize(company)})
    return rows


def _load_equity_list() -> list[dict]:
    """Load from local cache if fresh, otherwise re-download."""
    if os.path.exists(CACHE_PATH):
        age_days = (time.time() - os.path.getmtime(CACHE_PATH)) / 86400
        if age_days < CACHE_MAX_AGE_DAYS:
            try:
                with open(CACHE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass  # fall through to re-download on any cache corruption

    try:
        rows = _download_equity_list()
        with open(CACHE_PATH, "w") as f:
            json.dump(rows, f)
        return rows
    except Exception as e:
        print(f"NSE equity list download failed: {e}")
        # Last resort: use a stale cache if one exists, even past max age
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []


def lookup_ticker(company_name: str, min_score: float = 0.72) -> str | None:
    """
    Resolve a free-text company name to an NSE ticker (e.g. 'PWL.NS').
    Returns None if no confident match is found — callers should treat
    that as 'not listed', not as an error.
    """
    equity_list = _load_equity_list()
    if not equity_list:
        return None

    target = _normalize(company_name)
    if not target:
        return None

    best_symbol = None
    best_score = 0.0

    for row in equity_list:
        # Exact normalized match — short-circuit, this is the common case
        if row["norm"] == target:
            return f"{row['symbol']}.NS"

        # Substring match (e.g. "naukri" inside "info edge india naukri.com")
        # scores high but isn't perfect, so still compare against best_score
        score = difflib.SequenceMatcher(None, target, row["norm"]).ratio()
        if target in row["norm"] or row["norm"].startswith(target):
            score = max(score, 0.85)

        if score > best_score:
            best_score = score
            best_symbol = row["symbol"]

    if best_symbol and best_score >= min_score:
        return f"{best_symbol}.NS"
    return None


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else input("Company name: ")
    result = lookup_ticker(name)
    print(f"'{name}' -> {result or 'No confident match (likely not listed)'}")