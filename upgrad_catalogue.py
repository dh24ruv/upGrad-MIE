import os
import json
import re
from tavily import TavilyClient
from groq import Groq
from dotenv import load_dotenv

load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_upgrad_coverage(skill: str) -> dict:
    """
    Check if upGrad already has a course covering this skill.
    Searches learn.upgrad.com and upgrad.com directly.
    Returns coverage status + course names if found.
    """
    queries = [
        f"site:learn.upgrad.com {skill}",
        f"upGrad {skill} course certification program",
    ]

    results = []
    for q in queries:
        try:
            r = tavily_client.search(
                q, search_depth="advanced", max_results=4,
                include_domains=["upgrad.com", "learn.upgrad.com"]
            )
            for item in r.get("results", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content", "")[:400]
                })
        except Exception as e:
            print(f"  upGrad catalogue search error: {e}")

    if not results:
        return {
            "has_coverage": False,
            "matching_courses": [],
            "confidence": "Low",
            "note": "No matching upGrad course found via search."
        }

    search_text = "\n\n".join([
        f"TITLE: {r['title']}\nURL: {r['url']}\n{r['content']}" for r in results
    ])

    extraction_prompt = f"""
Based on these search results from upgrad.com and learn.upgrad.com, determine
if upGrad currently offers a course covering the skill "{skill}".

SEARCH RESULTS:
{search_text}

Return ONLY valid JSON:
{{
    "has_coverage": true or false,
    "matching_courses": [
        {{"name": "exact course name", "url": "exact url"}}
    ],
    "confidence": "High" or "Medium" or "Low",
    "note": "one sentence on coverage gap or overlap"
}}
"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=600,
            temperature=0.0
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "has_coverage": False,
            "matching_courses": [],
            "confidence": "Low",
            "note": f"Extraction failed: {str(e)[:100]}"
        }


if __name__ == "__main__":
    skill = input("Skill to check upGrad coverage for: ")
    result = get_upgrad_coverage(skill)
    print(json.dumps(result, indent=2))