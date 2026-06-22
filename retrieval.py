import os
import json
import re
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

# ── CLIENTS ──────────────────────────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Lazy load Tavily + Groq only when needed
_tavily = None
_groq   = None

def get_tavily():
    global _tavily
    if _tavily is None:
        from tavily import TavilyClient
        _tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _tavily

def get_groq():
    global _groq
    if _groq is None:
        from groq import Groq
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq

# ── FIELDS THAT MATTER ───────────────────────────────────────────────
# Plain text/number fields (existing behaviour unchanged)
CRITICAL_FIELDS = [
    "revenue_fy25", "revenue_fy24", "revenue_fy23",
    "net_loss_fy24", "net_income_fy25",
    "ebitda_fy25", "ebitda_fy24",
    "last_funding_round", "total_funding", "investor_names",
    "monthly_traffic", "headcount",
    "app_rating_android", "app_rating_ios",
    "hiring_signal", "last_notable_event",
]

SUPPLEMENTARY_FIELDS = [
    "traffic_trend", "headcount_trend",
    "market_cap", "last_funding_amount",
    "recent_course_launches", "geographic_expansion",
    "b2b_moves", "app_review_count",
]

# JSON fields — these store structured lists/objects, not tagged strings.
# news_items: [{"headline": "...", "date": "...", "source": "...", "url": "...", "relevance": "..."}]
# key_takeaways: [{"label": "Immediate threat", "content": "..."}]
JSON_FIELDS = [
    "news_items",
    "key_takeaways",
]

ALL_TEXT_FIELDS = CRITICAL_FIELDS + SUPPLEMENTARY_FIELDS

# ── DB OPERATIONS ────────────────────────────────────────────────────

def get_company(name: str) -> dict | None:
    """Fetch company from Supabase by name (fuzzy match)."""
    result = supabase.table("companies") \
        .select("*") \
        .ilike("name", f"%{name}%") \
        .limit(1) \
        .execute()
    if result.data:
        return result.data[0]
    return None

def get_all_companies() -> list:
    result = supabase.table("companies").select("*").execute()
    return result.data

def upsert_company(data: dict) -> None:
    """Save or update a company record in Supabase."""
    supabase.table("companies") \
        .upsert(data, on_conflict="name") \
        .execute()

# ── GAP DETECTION ────────────────────────────────────────────────────

def find_gaps(company: dict) -> list:
    """Return list of critical TEXT fields that are null or empty."""
    gaps = []
    for field in CRITICAL_FIELDS:
        val = company.get(field)
        if val is None or val == "" or val == "data unavailable":
            gaps.append(field)
    return gaps

def find_json_gaps(company: dict) -> list:
    """Return list of JSON fields that are null, empty list, or missing."""
    gaps = []
    for field in JSON_FIELDS:
        val = company.get(field)
        if val is None or val == [] or val == "":
            gaps.append(field)
    return gaps

def has_critical_gaps(company: dict) -> bool:
    """True if more than 3 critical fields are missing."""
    return len(find_gaps(company)) > 3

# ── WEB FILL: TEXT FIELDS (unchanged behaviour) ───────────────────────

def web_fill_gaps(company_name: str, gaps: list) -> dict:
    """
    For each gap field, run a targeted Tavily search.
    Then use Groq to extract the specific values from results.
    Returns a dict of filled values with source tags, e.g. "₹988 Cr [Entrackr, Sep 2024]".
    """
    tavily = get_tavily()
    groq   = get_groq()

    print(f"  Filling {len(gaps)} text gaps from web: {gaps}")

    financial_gaps = [f for f in gaps if any(x in f for x in ["revenue", "ebitda", "net_", "funding", "investor", "market_cap"])]
    traction_gaps  = [f for f in gaps if any(x in f for x in ["traffic", "headcount", "app_rating", "app_review"])]
    signal_gaps    = [f for f in gaps if any(x in f for x in ["hiring", "notable", "course", "expansion", "b2b"])]

    search_results = {}

    if financial_gaps:
        try:
            queries = [
                f"{company_name} edtech revenue EBITDA net loss FY25 FY24 FY23 MCA filing India crore",
                f"{company_name} funding raised investors Series valuation 2024 2025 2026",
            ]
            fin_results = []
            for q in queries:
                r = tavily.search(q, search_depth="advanced", max_results=3)
                for item in r.get("results", []):
                    url = item.get("url", "")
                    trusted = any(domain in url for domain in [
                        "entrackr.com", "inc42.com", "economictimes.com",
                        "moneycontrol.com", "mint.com", "livemint.com",
                        "yourstory.com", "tofler.in", "tracxn.com",
                        "crunchbase.com", "business-standard.com",
                        "ndtvprofit.com", "thehindubusinessline.com"
                    ])
                    if trusted or "mca.gov" in url:
                        fin_results.append(
                            f"SOURCE: {item.get('title')} ({url})\n{item.get('content','')[:600]}"
                        )
            search_results["financial"] = "\n\n---\n\n".join(fin_results)
        except Exception as e:
            print(f"  Financial search error: {e}")
            search_results["financial"] = ""

    if traction_gaps:
        try:
            queries = [
                f"{company_name} monthly traffic SimilarWeb visitors 2025 2026",
                f"{company_name} app rating Google Play App Store employees headcount 2026",
            ]
            tra_results = []
            for q in queries:
                r = tavily.search(q, search_depth="advanced", max_results=3)
                for item in r.get("results", []):
                    tra_results.append(
                        f"SOURCE: {item.get('title')} ({item.get('url')})\n{item.get('content','')[:500]}"
                    )
            search_results["traction"] = "\n\n---\n\n".join(tra_results)
        except Exception as e:
            print(f"  Traction search error: {e}")
            search_results["traction"] = ""

    if signal_gaps:
        try:
            queries = [
                f"{company_name} edtech news hiring expansion 2026",
                f"{company_name} acquisition merger partnership deal 2025 2026",
            ]
            sig_results = []
            for q in queries:
                r = tavily.search(q, search_depth="advanced", max_results=3)
                for item in r.get("results", []):
                    sig_results.append(
                        f"SOURCE: {item.get('title')} ({item.get('url')})\n{item.get('content','')[:500]}"
                    )
            search_results["signals"] = "\n\n---\n\n".join(sig_results)
        except Exception as e:
            print(f"  Signals search error: {e}")
            search_results["signals"] = ""

    combined_search = "\n\n====\n\n".join([
        f"FINANCIAL SOURCES:\n{search_results.get('financial','')}",
        f"TRACTION SOURCES:\n{search_results.get('traction','')}",
        f"SIGNAL SOURCES:\n{search_results.get('signals','')}"
    ])

    extraction_prompt = f"""
You are a data extraction specialist. Extract ONLY the following fields for "{company_name}" from the search results below.

FIELDS TO EXTRACT: {gaps}

SEARCH RESULTS:
{combined_search}

RULES:
- Extract ONLY from the search results above. Never invent data.
- For every value found, append source in brackets: "₹988 Cr [Entrackr, Sep 2024]"
- If not found in results, use null.
- IGNORE: instagram.com, facebook.com, twitter.com, reddit.com, quora.com
- For financials: only trust entrackr.com, inc42.com, economictimes.com, mint.com, moneycontrol.com, yourstory.com, tofler.in, business-standard.com
- For traffic: only trust similarweb.com, semrush.com
- For app ratings: only trust play.google.com, apps.apple.com, appfollow.io
- Numbers should include units: "₹988 Cr" not just "988"

Return ONLY valid JSON with exactly these keys (null if not found):
{json.dumps({f: None for f in gaps}, indent=2)}

No markdown, no explanation. Just the JSON.
"""

    try:
        resp = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=1500,
            temperature=0.0
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        filled = json.loads(raw)
        return {k: v for k, v in filled.items() if v is not None}
    except Exception as e:
        print(f"  Extraction error: {e}")
        return {}

# ── WEB FILL: JSON FIELDS (news_items, key_takeaways) ─────────────────

def web_fill_news(company_name: str) -> list:
    """
    Fetch latest news for the company and return a structured list:
    [{"headline": str, "date": str, "source": str, "url": str, "relevance": str}, ...]
    The URL comes directly from Tavily's result — the LLM never invents it.
    Groq only picks which results matter and writes the headline/relevance;
    we substitute the real url/source from our own search data afterwards.
    """
    tavily = get_tavily()
    groq   = get_groq()

    try:
        r = tavily.search(
            f"{company_name} edtech news 2026",
            search_depth="advanced",
            max_results=8
        )
        items = r.get("results", [])
    except Exception as e:
        print(f"  News search error: {e}")
        return []

    if not items:
        return []

    # Build an indexed list so the LLM references sources by number only —
    # it never types a URL itself, eliminating hallucinated/generic links.
    indexed = []
    for i, item in enumerate(items):
        indexed.append({
            "index": i,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": (item.get("content") or "")[:500],
            "published": item.get("published_date", "") or "",
        })

    source_block = "\n\n".join(
        f"[{x['index']}] {x['title']} ({x['published'] or 'date unknown'})\n{x['content']}"
        for x in indexed
    )

    prompt = f"""
You are selecting the most relevant recent news items about "{company_name}" for upGrad's competitive intelligence team.

SOURCES (numbered):
{source_block}

Pick up to 6 of the most relevant, recent, non-duplicate items.
For each, write a one-line headline (in your own words, not copied verbatim) and a one-line note on why it matters for upGrad.

Return ONLY valid JSON, a list of objects, referencing sources by their number:
[
  {{"index": 0, "headline": "...", "relevance": "..."}},
  ...
]
No markdown, no explanation, just the JSON list.
"""

    try:
        resp = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.1
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        picks = json.loads(raw)
    except Exception as e:
        print(f"  News extraction error: {e}")
        return []

    news_items = []
    for pick in picks:
        idx = pick.get("index")
        if idx is None or idx >= len(indexed) or idx < 0:
            continue
        src = indexed[idx]
        # url/source/date come from OUR data, not the LLM — guarantees real links
        domain = re.sub(r"^https?://(www\.)?", "", src["url"]).split("/")[0]
        news_items.append({
            "headline": pick.get("headline", src["title"]),
            "date": src["published"] or "recent",
            "source": domain,
            "url": src["url"],
            "relevance": pick.get("relevance", ""),
        })

    return news_items


def web_fill_takeaways(company_name: str, company: dict) -> list:
    """
    Generate key takeaways for upGrad based on whatever data we already have
    (financials + news), not a fresh search. Returns:
    [{"label": "Immediate threat", "content": "..."}, ...]
    """
    groq = get_groq()

    context_lines = []
    for f in CRITICAL_FIELDS:
        if company.get(f):
            context_lines.append(f"{f}: {company[f]}")
    for n in (company.get("news_items") or [])[:6]:
        context_lines.append(f"news: {n.get('headline')} — {n.get('relevance')}")

    context = "\n".join(context_lines) or "No data available."

    prompt = f"""
Based on this data about "{company_name}", write exactly 4 key takeaways for upGrad's Founder's Office.

DATA:
{context}

Return ONLY a valid JSON list of exactly 4 objects, in this order:
[
  {{"label": "Immediate threat", "content": "..."}},
  {{"label": "Opportunity", "content": "..."}},
  {{"label": "Action this week", "content": "..."}},
  {{"label": "Watch (30 days)", "content": "..."}}
]
Keep each "content" under 25 words. No markdown, no explanation, just the JSON list.
"""
    try:
        resp = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  Takeaways extraction error: {e}")
        return []

# ── MAIN FUNCTION ─────────────────────────────────────────────────────

def get_company_full(name: str, save_to_db: bool = True) -> dict:
    """
    Main entry point.
    1. Try DB first
    2. If not found → full web scrape (text fields + news + takeaways)
    3. If found but has gaps → fill gaps from web (text and/or JSON)
    4. Save enriched data back to DB
    Returns the most complete company dict available.
    """
    company = get_company(name)

    if company:
        print(f"✓ '{name}' found in database.")
        gaps      = find_gaps(company)
        json_gaps = find_json_gaps(company)

        if not gaps and not json_gaps:
            print(f"  All critical fields present. No web lookup needed.")
            company["_source"] = "database"
            return company

        update_payload = {"name": company["name"]}

        if gaps:
            print(f"  {len(gaps)} text gaps found in database record.")
            web_data = web_fill_gaps(name, gaps)
            if web_data:
                for field, value in web_data.items():
                    if company.get(field) is None:
                        company[field] = value
                update_payload.update({
                    k: v for k, v in web_data.items()
                    if k in ALL_TEXT_FIELDS
                })

        if "news_items" in json_gaps:
            print("  Filling news_items from web.")
            news = web_fill_news(name)
            if news:
                company["news_items"] = news
                update_payload["news_items"] = news

        if "key_takeaways" in json_gaps:
            print("  Filling key_takeaways from web.")
            takeaways = web_fill_takeaways(name, company)
            if takeaways:
                company["key_takeaways"] = takeaways
                update_payload["key_takeaways"] = takeaways

        if save_to_db and len(update_payload) > 1:
            try:
                upsert_company(update_payload)
                print(f"  Saved {len(update_payload)-1} enriched fields back to DB.")
            except Exception as e:
                print(f"  DB save error (non-critical): {e}")

        company["_source"] = "database+web"
        return company

    else:
        print(f"'{name}' not in database — running full web lookup...")
        web_data = web_fill_gaps(name, CRITICAL_FIELDS + SUPPLEMENTARY_FIELDS)
        web_data["name"] = name
        web_data["news_items"] = web_fill_news(name)
        web_data["key_takeaways"] = web_fill_takeaways(name, web_data)

        if save_to_db:
            try:
                upsert_company(web_data)
                print(f"  Saved new company record to DB.")
            except Exception as e:
                print(f"  DB save error (non-critical): {e}")

        web_data["_source"] = "web"
        return web_data


# ── TEST ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else input("Company name: ")
    result = get_company_full(name)
    print(f"\nSource: {result.get('_source')}")
    print("\nData:")
    for k, v in result.items():
        if v is not None and not k.startswith("_"):
            print(f"  {k}: {v}")