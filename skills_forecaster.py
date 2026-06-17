import os
import re
from datetime import date
from tavily import TavilyClient
from groq import Groq
from dotenv import load_dotenv

load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

today = date.today().strftime("%d %b %Y")

SKILLS_PROMPT = """
You are a skills demand forecaster for upGrad, an Indian edtech company.

Based ONLY on the search data below, generate a structured skills demand report.

STRICT RULES:
- Only use data explicitly found in search results. Never invent statistics.
- Tag every data point with its source in brackets.
- If data unavailable, write "data unavailable" — never guess.
- Frame every insight in terms of what it means for upGrad specifically.
- Recommendations must be specific and actionable.

SEARCH DATA:
{search_data}

SKILL/TOPIC: {skill}
SECTOR: {sector}
GEOGRAPHY: {geography}
GENERATED: {today}

OUTPUT FORMAT (follow exactly):

SKILLS DEMAND REPORT: {skill}
SECTOR: {sector} | GEOGRAPHY: {geography}
GENERATED: {today}

━━━ DEMAND SIGNALS ━━━
Job posting volume:
Job posting growth (YoY):
Top companies hiring for this skill:
Average salary range:
GitHub / open source activity:
Industry adoption signals:
Confidence: [High/Medium/Low — reason]

━━━ MARKET CONTEXT ━━━
Current demand stage: [Emerging / Growing / Mainstream / Declining]
Time to mainstream demand: [X months estimate]
Peak demand window: [estimated range]
Key industries driving demand:
Adjacent skills in demand:

━━━ COMPETITOR COVERAGE ━━━
[Which edtech platforms already offer courses on this skill]
Coursera:
LinkedIn Learning:
Simplilearn:
Great Learning:
BYJU'S / upGrad competitors:
Gap in market:

━━━ UPGRAD OPPORTUNITY ━━━
Recommended action: [Launch now / Plan for Q3 / Monitor for 3 months]
Urgency: [High / Medium / Low]
Estimated course demand:
Suggested course format: [certification / PG programme / short course]
Suggested price range:
Potential university partner:

━━━ LEADING INDICATORS ━━━
[3 signals that predict this skill will grow — cite each]
1.
2.
3.

━━━ FALSE POSITIVE RISKS ━━━
[Reasons this trend might not translate to course demand]
1.
2.

━━━ LATEST NEWS & SIGNALS ━━━
[Recent news items relevant to this skill — DATE — Headline — Source — Relevance]

━━━ CONFIDENCE SUMMARY ━━━
Overall confidence: [High/Medium/Low]
Data unavailable:
Needs verification:
"""

def forecast_skill(skill: str, sector: str = "Technology", geography: str = "India") -> str:
    print(f"Searching demand signals for '{skill}'...")

    queries = [
        f"{skill} job postings demand India 2026 hiring growth",
        f"{skill} skills shortage edtech courses certification 2026",
        f"{skill} industry adoption companies hiring salary India",
        f"{skill} Coursera Simplilearn upGrad course launched 2025 2026",
        f"{skill} emerging technology trend {sector} {geography} 2026",
    ]

    all_results = []
    for query in queries:
        try:
            result = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=3,
                include_raw_content=False
            )
            for r in result.get("results", []):
                all_results.append(
                    f"SOURCE: {r.get('title')} ({r.get('url')})\n{r.get('content','')[:500]}"
                )
        except Exception as e:
            print(f"Search error: {e}")
            continue

    search_data = "\n\n---\n\n".join(all_results)

    prompt = SKILLS_PROMPT.format(
        search_data=search_data,
        skill=skill,
        sector=sector,
        geography=geography,
        today=today
    )

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a senior skills demand analyst at upGrad. You identify emerging skill trends before they become mainstream. Every recommendation must be specific, cited, and actionable for a product team that launches online courses."
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
    skill = input("Enter skill or topic: ")
    sector = input("Sector (press Enter for 'Technology'): ").strip() or "Technology"
    geography = input("Geography (press Enter for 'India'): ").strip() or "India"

    report = forecast_skill(skill, sector, geography)
    print("\n" + "="*60)
    print(report)
    print("="*60)
