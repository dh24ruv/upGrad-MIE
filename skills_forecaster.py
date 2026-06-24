import os
import re
from datetime import date
from tavily import TavilyClient
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
groq_client   = Groq(api_key=os.getenv("GROQ_API_KEY"))

today = date.today().strftime("%d %b %Y")

SKILLS_PROMPT = """
You are a skills demand forecaster for upGrad, an Indian edtech company.

Based ONLY on the search data below, generate a structured skills demand report.

CRITICAL GEOGRAPHY RULE:
- The target geography is {geography}.
- ONLY use job data, salary figures, hiring signals, and industry trends FROM {geography}.
- If a source is from a different geography, explicitly label it as such and do NOT apply it to {geography} without noting the difference.
- If {geography} is not India, do NOT use Indian salary figures, Indian job boards (Naukri/Shine), or Indian company hiring data unless the company has operations specifically in {geography}.

STRICT RULES:
- Only use data explicitly found in search results. Never invent statistics.
- Tag every data point with its source in brackets.
- If data unavailable for {geography} specifically, write "data unavailable for {geography}" — never guess.
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
[Which edtech platforms already offer courses on this skill in {geography}]
Coursera:
LinkedIn Learning:
Simplilearn:
Great Learning:
Local competitors in {geography}:
Gap in market:

━━━ UPGRAD OPPORTUNITY ━━━
Recommended action: [Launch now / Plan for Q3 / Monitor for 3 months]
Urgency: [High / Medium / Low]
Estimated course demand:
Suggested course format: [certification / PG programme / short course]
Suggested price range:
Potential university partner:
upGrad's current presence in {geography}:

━━━ LEADING INDICATORS ━━━
[3 signals from {geography} that predict this skill will grow — cite each]
1.
2.
3.

━━━ FALSE POSITIVE RISKS ━━━
[Reasons this trend might not translate to course demand in {geography}]
1.
2.

━━━ LATEST NEWS & SIGNALS ━━━
[Recent news items relevant to this skill in {geography} — DATE — Headline — Source — Relevance]

━━━ CONFIDENCE SUMMARY ━━━
Overall confidence: [High/Medium/Low]
Data unavailable:
Needs verification:
"""


def forecast_skill(skill: str, sector: str = "Technology", geography: str = "India") -> str:
    print(f"Searching demand signals for '{skill}' in {geography}...")

    # Geography-aware job board and salary source hints
    geo_sources = {
        "India":          "Naukri LinkedIn Indeed India salary",
        "MENA":           "Bayt GulfTalent LinkedIn MENA Gulf salary UAE Saudi Arabia",
        "Southeast Asia": "JobStreet LinkedIn Singapore Malaysia Indonesia salary",
        "Global":         "LinkedIn Indeed Glassdoor global salary",
    }
    geo_hint = geo_sources.get(geography, f"LinkedIn Indeed {geography} salary")

    # Geography-aware edtech competitor hint
    geo_competitors = {
        "India":          "Simplilearn Great Learning BYJU's upGrad",
        "MENA":           "Coursera edX Udemy Alison MENA edtech",
        "Southeast Asia": "Coursera Udemy Preply Southeast Asia edtech",
        "Global":         "Coursera LinkedIn Learning Udemy edX",
    }
    comp_hint = geo_competitors.get(geography, f"Coursera Udemy {geography} edtech")

    queries = [
        f"{skill} job postings demand {geography} 2026 hiring growth {geo_hint}",
        f"{skill} skills shortage {geography} courses certification 2026",
        f"{skill} industry adoption companies hiring salary {geography} 2026",
        f"{comp_hint} {skill} course launched 2025 2026",
        f"{skill} emerging technology trend {sector} {geography} 2026",
        f"{skill} {geography} market size workforce demand report 2025 2026",
    ]

    all_results = []
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
                all_results.append(
                    f"SOURCE: {r.get('title')} ({r.get('url')})\n{content[:1200]}"
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
                "content": (
                    f"You are a senior skills demand analyst at upGrad. "
                    f"You are producing a report specifically for {geography}. "
                    f"STRICT RULE: Only cite job data, salaries, hiring signals, and market figures "
                    f"that are explicitly from {geography}. "
                    f"If a source is from India but the geography is {geography}, do NOT apply Indian "
                    f"data to {geography} — label it 'India data, not applicable' and mark the field "
                    f"as data unavailable for {geography}. "
                    f"Every recommendation must be specific, cited, and actionable for a product team "
                    f"launching online courses in {geography}."
                )
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
    skill     = input("Enter skill or topic: ")
    sector    = input("Sector (press Enter for 'Technology'): ").strip() or "Technology"
    geography = input("Geography (press Enter for 'India'): ").strip() or "India"

    report = forecast_skill(skill, sector, geography)
    print("\n" + "="*60)
    print(report)
    print("="*60)