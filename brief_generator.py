import os
import json
import re
from datetime import date
from groq import Groq
from dotenv import load_dotenv
from retrieval import get_company_full
from tavily import TavilyClient

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

today = date.today().strftime("%d %b %Y")

BRIEF_PROMPT = """
You are a senior market intelligence analyst at upGrad, an Indian edtech company.

Given the following data, generate a structured intelligence brief.

STRICT RULES:
- Only use data explicitly provided. Never infer or estimate financial figures.
- If a field is missing, write "data unavailable" — never guess.
- Tag EVERY data point with its exact source and date in brackets.
- Financials and latest news carry the highest weight — be most thorough here.
- Key Takeaways must be specific and actionable, not generic statements.
- Confidence: High = primary source (MCA/filing), Medium = reputable news, Low = estimate.

COMPANY DATA:
{company_data}

OUTPUT FORMAT (follow exactly):

COMPANY: [name]
GENERATED: {today}

━━━ FINANCIALS ━━━
Revenue (FY25):
Revenue (FY24):
Revenue (FY23):
Revenue trend (FY23→FY25): [growing / declining / flat + % change]
EBITDA (FY25):
EBITDA (FY24):
Net Income/Loss (FY25):
Net Income/Loss (FY24):
Burn rate estimate:
Market Cap:
Last funding round:
Total funding raised:
Investor names:
Confidence: [High/Medium/Low — reason]

━━━ LATEST NEWS (last 90 days) ━━━
[List each news item on its own line as: DATE — Headline — Source URL — Why it matters for upGrad]
[If no recent news found, list the 3 most recent news items available regardless of date]
[Minimum 3 news items required — search harder if needed]

━━━ TRACTION ━━━
Monthly web traffic:
Traffic trend (MoM):
App rating (iOS):
App rating (Android):
Total app reviews:
Headcount (current):
Headcount trend:
Confidence: [High/Medium/Low — reason]

━━━ COMPETITIVE SIGNALS ━━━
Hiring signals: [roles being hired = strategic direction]
Marketing spend signals:
Geographic expansion signals:
B2B / enterprise moves:

━━━ KEY TAKEAWAYS FOR UPGRAD ━━━
[Must be specific, not generic. Reference actual data points.]
1. Immediate threat:
2. Opportunity to exploit:
3. Recommended action this week:
4. Watch list (next 30 days):

━━━ PRIORITY SCORE ━━━
Overall threat level: [High / Medium / Low]
Reason: [one sentence with specific evidence]

━━━ CONFIDENCE SUMMARY ━━━
Data unavailable: [list fields]
Needs verification: [list fields with medium confidence]
"""

EXTRACTION_PROMPT = """
You are a data extraction specialist. Based ONLY on the search results below,
extract information about "{company_name}" and return a JSON object.

SEARCH RESULTS:
{search_text}

Return ONLY a valid JSON object with these keys (null if not found in results):
{{
    "name": "{company_name}",
    "revenue_fy25": null,
    "ebitda_fy25": null,
    "net_income_fy25": null,
    "revenue_fy24": null,
    "ebitda_fy24": null,
    "net_loss_fy24": null,
    "revenue_fy23": null,
    "net_loss_fy23": null,
    "financial_source": null,
    "market_cap": null,
    "last_funding_round": null,
    "last_funding_amount": null,
    "last_funding_year": null,
    "total_funding": null,
    "investor_names": null,
    "recent_course_launches": null,
    "upcoming_launches": null,
    "new_verticals": null,
    "new_university_partnerships": null,
    "new_programme_pricing": null,
    "latest_news_90_days": null,
    "monthly_traffic": null,
    "traffic_trend": null,
    "app_rating_ios": null,
    "app_rating_android": null,
    "app_review_count": null,
    "headcount": null,
    "headcount_trend": null,
    "hiring_signal": null,
    "geographic_expansion": null,
    "b2b_moves": null,
    "last_notable_event": null,
    "notes": null
}}

RULES:
- IGNORE these sources entirely: instagram.com, facebook.com, twitter.com, reddit.com, quora.com
- For financial data, only use: MCA filings, Tofler, Entrackr, Inc42, Economic Times, Mint, YourStory, Moneycontrol
- For traffic data, only use: SimilarWeb, SEMrush
- For app ratings, only use: Google Play Store, Apple App Store
- Return raw JSON only — no markdown, no explanation
- Only use data from search results below. Never invent financial figures.
- EVERY citation MUST be in this exact format: [Source Name](https://full-url-here)
- NEVER write a citation as [Source Name, Date] or [Source, Year] — that is WRONG and will break the application.
- If you do not have the exact URL for a source, write the data point WITHOUT a citation rather than using a malformed one.
- Example of CORRECT citation: Revenue (FY25): ₹826.3 Cr [Entrackr](https://entrackr.com/2025/09/unacademy-financials)
- Example of INCORRECT citation (do not do this): Revenue (FY25): ₹826.3 Cr [Entrackr, Sep 2025]
GLOBAL CITATION RULE — applies to EVERY field in EVERY section (financials, traction, signals, investors, news, everything):
- Every citation must be: [Source Name](https://full-url)
- NEVER write [Source Name, Year] or [Source, Date] anywhere in this document — not even in the financials or investors tables.
- If you cannot find the exact URL for a financial figure, write it without a citation tag rather than using a name-only bracket.
"""


def fetch_entrackr_data(company_name: str) -> str:
    """Dedicated deep fetch from Entrackr and Inc42 for MCA-verified financials."""
    print(f"  → Deep fetching Entrackr / Inc42 for {company_name}...")
    targeted_queries = [
        f"site:entrackr.com {company_name} revenue FY25 FY24 EBITDA net loss",
        f"site:inc42.com {company_name} revenue annual report funding 2025",
    ]
    results = []
    for query in targeted_queries:
        try:
            res = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=2,
                include_raw_content=True,
                max_tokens=3000
            )
            for r in res.get("results", []):
                content = r.get("raw_content") or r.get("content", "")
                results.append(
                    f"SOURCE: {r.get('title')} ({r.get('url')})\n{content[:3000]}"
                )
        except Exception as e:
            print(f"  Entrackr/Inc42 search error: {e}")
            continue
    return "\n\n---\n\n".join(results)


def scrape_company_data(company_name: str) -> dict:
    """Fetch company data via Tavily (with Entrackr priority) then extract via Groq."""
    print(f"Searching web for {company_name}...")

    # Step 1: Priority fetch from Entrackr + Inc42 first
    entrackr_data = fetch_entrackr_data(company_name)

    # Step 2: Broad queries for everything else
    queries = [
        f"{company_name} edtech revenue EBITDA net loss FY25 FY24 MCA filing India crore",
        f"site:moneycontrol.com {company_name} quarterly results revenue profit 2025 2026",
        f"{company_name} edtech news June May April 2026",
        f"{company_name} similarweb monthly traffic visitors 2026",
        f"{company_name} app rating Google Play App Store reviews 2026",
        f"{company_name} employees headcount LinkedIn layoffs 2026",
    ]

    all_results = []

    # Prepend Entrackr data as the highest-priority result
    if entrackr_data:
        all_results.append({
            "title": "Entrackr / Inc42 — MCA financials",
            "url": "entrackr.com / inc42.com",
            "content": entrackr_data[:3000]
        })

    for query in queries:
        try:
            result = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=3,
                include_raw_content=True,
                max_tokens=3000
            )
            for r in result.get("results", []):
                content = r.get("raw_content") or r.get("content", "")
                all_results.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": content[:1200]
                })
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            continue

    # Step 3: Format for Groq
    search_text = "\n\n".join([
        f"SOURCE: {r['title']} ({r['url']})\n{r['content']}"
        for r in all_results
    ])

    # Step 4: Groq extraction → structured JSON
    extraction_prompt = EXTRACTION_PROMPT.format(
        company_name=company_name,
        search_text=search_text
    )

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": extraction_prompt}],
        max_tokens=2000,
        temperature=0.0
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"name": company_name, "notes": f"Extraction failed: {raw[:800]}"}


def generate_brief(company_name: str) -> str:
    company = get_company_full(company_name)
    source = company.get("_source", "unknown")

    if source == "database":
        print(f"✓ All data from database. No web lookup needed.")
    elif source == "database+web":
        print(f"✓ Database + web gap-fill.")
    else:
        print(f"✓ Full web lookup.")

    company_data = "\n".join([
        f"{k}: {v}"
        for k, v in company.items()
        if v is not None and k not in ["id", "created_at", "updated_at"]
    ])

    prompt = BRIEF_PROMPT.format(
        company_data=company_data,
        today=today
    )

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a senior market intelligence analyst at upGrad. You write precise, actionable briefs for the Founder's Office. Every claim must be cited. Vague statements are not acceptable."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=3000,
        temperature=0.1
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    company_name = input("Enter company name: ")
    brief = generate_brief(company_name)
    print("\n" + "="*60)
    print(brief)
    print("="*60)