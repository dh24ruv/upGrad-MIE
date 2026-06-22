import streamlit as st
import sys
import re
import os
from dotenv import load_dotenv
from tavily import TavilyClient
from groq import Groq
from datetime import date

load_dotenv()
sys.path.append("/Users/dhruvpande/upgrad")

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
groq_client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
today_str     = date.today().strftime("%d %b %Y")

# ── Helpers ──────────────────────────────────────────────────────────
def make_links(text):
    """Convert markdown links AND bare URLs to clickable HTML anchors."""
    if not text or text == "—":
        return text
    s = str(text)

    # 1. markdown-style [label](url)
    s = re.sub(
        r'\[([^\]]+)\]\((https?://[^\s\)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener noreferrer" style="color:#C0001A;text-decoration:underline">\1</a>',
        s
    )

    # 2. bare URLs not already inside an href="..."
    #    - stop at whitespace, <, >, quotes
    #    - then strip trailing punctuation (.,);] that often gets caught from prose
    def linkify_bare(match):
        url = match.group(1)
        trailing = ""
        while url and url[-1] in '.,);]"\'':
            trailing = url[-1] + trailing
            url = url[:-1]
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color:#C0001A;text-decoration:underline">{url}</a>{trailing}'

    s = re.sub(
        r'(?<!href=")(https?://[^\s<>"\']+)',
        linkify_bare,
        s
    )
    return s

def extract(text, start_marker, end_markers):
    try:
        start = text.index(start_marker) + len(start_marker)
        end   = len(text)
        for m in end_markers:
            try:
                pos = text.index(m, start)
                if pos < end:
                    end = pos
            except ValueError:
                pass
        return text[start:end].strip()
    except ValueError:
        return ""

def parse_field(block, label):
    for line in block.split("\n"):
        if line.strip().startswith(label):
            val = line.split(":", 1)[-1].strip()
            return val if val and val != "data unavailable" else "—"
    return "—"

def trend_class(val):
    v = val.lower()
    if "declin" in v or v.startswith("-"): return "change-neg"
    if "grow" in v or "increas" in v or v.startswith("+"): return "change-pos"
    return ""

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="upGrad MIE",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding: 0 2rem 2rem; max-width: 1100px; margin: 0 auto; }
    body { background: #fff; }

    .mie-nav { display:flex;align-items:center;gap:2rem;padding:0.8rem 0;border-bottom:1px solid #e0e0e0;margin-bottom:1.5rem; }
    .mie-nav-logo { font-size:1rem;font-weight:500;color:#C0001A;letter-spacing:-0.3px; }
    .mie-nav-links { display:flex;gap:1.5rem; }
    .mie-nav-link { font-size:0.85rem;color:#444;text-decoration:none; }
    .mie-nav-link:hover { color:#C0001A; }

    .company-header { margin-bottom:1.5rem; }
    .company-name { font-size:1.6rem;font-weight:400;color:#202124;margin-bottom:0.2rem; }
    .company-meta { font-size:0.8rem;color:#70757a;margin-bottom:1rem; }
    .company-score-row { display:flex;align-items:baseline;gap:1rem;margin-bottom:0.5rem; }
    .company-updated { font-size:0.75rem;color:#70757a; }

    .threat-badge-high { color:#c0392b;font-size:0.85rem;font-weight:500;background:#fce8e6;padding:2px 10px;border-radius:12px; }
    .threat-badge-med  { color:#e67e22;font-size:0.85rem;font-weight:500;background:#fef3e2;padding:2px 10px;border-radius:12px; }
    .threat-badge-low  { color:#27ae60;font-size:0.85rem;font-weight:500;background:#e6f4ea;padding:2px 10px;border-radius:12px; }

    .stats-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;margin-bottom:1.5rem; }
    .stat-cell { padding:0.9rem 1rem;border-right:1px solid #e0e0e0; }
    .stat-cell:last-child { border-right:none; }
    .stat-label { font-size:0.72rem;color:#70757a;margin-bottom:0.2rem; }
    .stat-value { font-size:0.95rem;font-weight:500;color:#202124; }

    .fin-section { margin-bottom:1.5rem; }
    .fin-section-title { font-size:1rem;font-weight:500;color:#202124;margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:1px solid #e0e0e0; }
    .fin-table { width:100%;border-collapse:collapse;font-size:0.82rem; }
    .fin-table th { text-align:right;padding:0.5rem 0.8rem;color:#70757a;font-weight:400;border-bottom:1px solid #e0e0e0; }
    .fin-table th:first-child { text-align:left; }
    .fin-table td { padding:0.55rem 0.8rem;border-bottom:1px solid #f1f3f4;color:#202124;text-align:right; }
    .fin-table td:first-child { text-align:left;color:#444; }
    .fin-table tr:hover td { background:#f8f9fa; }
    .change-pos { color:#1e8e3e; }
    .change-neg { color:#c0392b; }
    .na { color:#bbb; }

    .news-section-title { font-size:1rem;font-weight:500;color:#202124;margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:1px solid #e0e0e0; }
    .news-card { display:flex;gap:1rem;padding:0.8rem 0;border-bottom:1px solid #f1f3f4;align-items:flex-start; }
    .news-card:last-child { border-bottom:none; }
    .news-dot { width:6px;height:6px;border-radius:50%;background:#C0001A;margin-top:5px;flex-shrink:0; }
    .news-content { flex:1; }
    .news-headline { font-size:0.85rem;color:#202124;font-weight:500;margin-bottom:0.2rem;line-height:1.4; }
    .news-meta { font-size:0.75rem;color:#70757a; }
    .news-relevance { font-size:0.75rem;color:#444;margin-top:0.2rem;font-style:italic; }

    .ai-verified { font-size:0.72rem;color:#70757a;border:1px solid #e0e0e0;padding:2px 8px;border-radius:12px;display:inline-block; }
    .source-tag  { font-size:0.7rem;color:#70757a;background:#f1f3f4;padding:1px 5px;border-radius:4px; }

    .stTabs [data-baseweb="tab-list"] { border-bottom:2px solid #e0e0e0;gap:0; }
    .stTabs [data-baseweb="tab"] { font-size:0.85rem;padding:0.6rem 1.2rem;color:#70757a;border-bottom:2px solid transparent;margin-bottom:-2px; }
    .stTabs [aria-selected="true"] { color:#C0001A;border-bottom:2px solid #C0001A;font-weight:500; }

    div[data-testid="stTextInput"] input { border-radius:24px;border:1px solid #e0e0e0;padding:0.5rem 1rem;font-size:0.9rem; }
    div[data-testid="stTextInput"] input:focus { border-color:#C0001A;box-shadow:none; }

    .stButton > button { background:#C0001A;color:white;border:none;border-radius:4px;font-size:0.85rem;padding:0.4rem 1.2rem;font-weight:500; }
    .stButton > button:hover { background:#a30017;color:white;border:none; }

    .watchlist-item { display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #f1f3f4;font-size:0.82rem; }
    .watchlist-name { color:#202124;font-weight:500; }
    .watchlist-meta { color:#70757a;font-size:0.75rem; }

    footer { visibility:hidden; }
    #MainMenu { visibility:hidden; }
    header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Nav ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="mie-nav">
    <span class="mie-nav-logo">upGrad MIE</span>
    <div class="mie-nav-links">
        <span class="mie-nav-link">Company Briefs</span>
        <span class="mie-nav-link">Skills Demand</span>
        <span class="mie-nav-link">M&A Intel</span>
        <span class="mie-nav-link">Chat</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Company Briefs", "Skills Demand", "M&A Intelligence", "Chat"
])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — COMPANY BRIEFS  (structured dict version — no text parsing)
# ════════════════════════════════════════════════════════════════════
with tab1:
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        company_name = st.text_input(
            "search",
            placeholder="Search company — e.g. Simplilearn, Unacademy, BYJU'S",
            label_visibility="collapsed"
        )
    with col_btn:
        search_btn = st.button("Search", key="search_btn")

    def field(c, key, default="—"):
        """Pull a field from the company dict, falling back cleanly."""
        val = c.get(key)
        if val is None or val == "" or val == "data unavailable":
            return default
        return make_links(str(val))

    if search_btn and company_name.strip():
        with st.spinner(f"Loading brief for {company_name}..."):
            try:
                from retrieval import get_company_full
                company = get_company_full(company_name)
            except Exception as e:
                st.error(f"Something went wrong: {str(e)[:200]}")
                company = None

        if company:
            source_label = {
                "database":      "Database",
                "database+web":  "Database + Live fill",
                "web":            "Live lookup",
            }.get(company.get("_source"), "Live lookup")

            # ── Header ───────────────────────────────────────────────
            st.markdown(f"""
            <div class="company-header">
                <div class="company-name">{company_name.title()}</div>
                <div class="company-meta">
                    Edtech · India &nbsp;·&nbsp;
                    <span class="ai-verified">AI-assisted, analyst-verified</span> &nbsp;·&nbsp;
                    <span class="source-tag">{source_label}</span>
                </div>
                <div class="company-updated">Generated {today_str} · Data from MCA, Entrackr, Tracxn, SimilarWeb, LinkedIn</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Quick stats ──────────────────────────────────────────
            st.markdown(f"""
            <div class="stats-grid">
                <div class="stat-cell"><div class="stat-label">Revenue FY25</div><div class="stat-value">{field(company, "revenue_fy25")}</div></div>
                <div class="stat-cell"><div class="stat-label">EBITDA FY25</div><div class="stat-value">{field(company, "ebitda_fy25")}</div></div>
                <div class="stat-cell"><div class="stat-label">Monthly traffic</div><div class="stat-value">{field(company, "monthly_traffic")}</div></div>
                <div class="stat-cell"><div class="stat-label">Last funding</div><div class="stat-value">{field(company, "last_funding_round")}</div></div>
            </div>
            """, unsafe_allow_html=True)

            # ── Financials table ─────────────────────────────────────
            st.markdown(f"""
            <div class="fin-section">
                <div class="fin-section-title">Financials</div>
                <table class="fin-table">
                    <thead><tr><th>Metric</th><th>FY25</th><th>FY24</th><th>FY23</th></tr></thead>
                    <tbody>
                        <tr><td>Revenue</td><td>{field(company, "revenue_fy25")}</td><td>{field(company, "revenue_fy24")}</td><td>{field(company, "revenue_fy23")}</td></tr>
                        <tr><td>EBITDA</td><td>{field(company, "ebitda_fy25")}</td><td>{field(company, "ebitda_fy24")}</td><td class="na">—</td></tr>
                        <tr><td>Net Income / Loss</td><td>{field(company, "net_income_fy25")}</td><td>{field(company, "net_loss_fy24")}</td><td class="na">—</td></tr>
                        <tr><td>Market Cap</td><td colspan="3">{field(company, "market_cap")}</td></tr>
                        <tr><td>Total funding</td><td colspan="3">{field(company, "total_funding")}</td></tr>
                        <tr><td>Key investors</td><td colspan="3">{field(company, "investor_names")}</td></tr>
                    </tbody>
                </table>
            </div>
            """, unsafe_allow_html=True)

            # ── News (real structured items — real URLs, always clickable) ──
            st.markdown('<div class="news-section-title">Latest news & signals</div>', unsafe_allow_html=True)
            news_items = company.get("news_items") or []
            if news_items:
                news_html = ""
                for n in news_items[:6]:
                    headline  = n.get("headline", "")
                    date_str  = n.get("date", "")
                    source    = n.get("source", "")
                    url       = n.get("url", "")
                    relevance = n.get("relevance", "")
                    source_link = (
                        f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                        f'style="color:#C0001A;text-decoration:underline">{source}</a>'
                        if url else source
                    )
                    news_html += f"""
                    <div class="news-card">
                        <div class="news-dot"></div>
                        <div class="news-content">
                            <div class="news-headline">{headline}</div>
                            <div class="news-meta">{date_str} · {source_link}</div>
                            <div class="news-relevance">{relevance}</div>
                        </div>
                    </div>"""
                st.markdown(news_html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#70757a;font-size:0.85rem">No recent news found.</div>', unsafe_allow_html=True)

            # ── Traction + Competitive signals ───────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            col_t, col_s = st.columns(2)

            with col_t:
                st.markdown(f"""
                <div class="fin-section">
                    <div class="fin-section-title">Traction</div>
                    <table class="fin-table">
                        <tbody>
                            <tr><td>Monthly traffic</td><td>{field(company, "monthly_traffic")}</td></tr>
                            <tr><td>Traffic trend</td><td>{field(company, "traffic_trend")}</td></tr>
                            <tr><td>App rating (Android)</td><td>{field(company, "app_rating_android")}</td></tr>
                            <tr><td>App rating (iOS)</td><td>{field(company, "app_rating_ios")}</td></tr>
                            <tr><td>Total reviews</td><td>{field(company, "app_review_count")}</td></tr>
                            <tr><td>Headcount</td><td>{field(company, "headcount")}</td></tr>
                            <tr><td>Headcount trend</td><td>{field(company, "headcount_trend")}</td></tr>
                        </tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

            with col_s:
                st.markdown(f"""
                <div class="fin-section">
                    <div class="fin-section-title">Competitive signals</div>
                    <table class="fin-table">
                        <tbody>
                            <tr><td>Hiring signals</td><td>{field(company, "hiring_signal")}</td></tr>
                            <tr><td>Geo expansion</td><td>{field(company, "geographic_expansion")}</td></tr>
                            <tr><td>B2B / enterprise</td><td>{field(company, "b2b_moves")}</td></tr>
                            <tr><td>Recent launches</td><td>{field(company, "recent_course_launches")}</td></tr>
                        </tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

            # ── Key takeaways ─────────────────────────────────────────
            takeaways = company.get("key_takeaways") or []
            if takeaways:
                rows = ""
                for t in takeaways[:4]:
                    label   = t.get("label", "")
                    content = t.get("content", "")
                    rows   += f"<tr><td style='width:160px;color:#70757a'>{label}</td><td>{content}</td></tr>"

                st.markdown(f"""
                <div class="fin-section">
                    <div class="fin-section-title">Key takeaways for upGrad</div>
                    <table class="fin-table"><tbody>{rows}</tbody></table>
                </div>
                """, unsafe_allow_html=True)

    else:
        # Default watchlist state
        st.markdown('<div class="fin-section-title" style="margin-top:1rem">Tracked companies</div>', unsafe_allow_html=True)
        try:
            from retrieval import get_all_companies
            companies = get_all_companies()
            if companies:
                for c in companies[:15]:
                    name      = c.get("name", "")
                    rev       = c.get("revenue_fy24", "—")
                    tier      = c.get("tier", "")
                    tier_label= {1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}.get(tier, "")
                    st.markdown(f"""
                    <div class="watchlist-item">
                        <div><span class="watchlist-name">{name}</span> &nbsp;<span class="source-tag">{tier_label}</span></div>
                        <div class="watchlist-meta">Rev FY24: {rev}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#70757a;font-size:0.85rem">No companies in database yet.</div>', unsafe_allow_html=True)
        except Exception:
            st.markdown('<div style="color:#aaa;font-size:0.8rem">Could not load database.</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# TAB 2 — SKILLS DEMAND
# ════════════════════════════════════════════════════════════════════
with tab2:
    col_sk, col_sec, col_geo, col_btn2 = st.columns([3, 1.5, 1.5, 1])
    with col_sk:
        skill_q = st.text_input("skill", placeholder="e.g. Agentic AI, Cloud FinOps, Healthcare Data", label_visibility="collapsed")
    with col_sec:
        sector = st.selectbox("Sector", ["Technology", "Healthcare", "Finance", "Manufacturing", "All"], label_visibility="collapsed")
    with col_geo:
        geography = st.selectbox("Geography", ["India", "Southeast Asia", "Global", "MENA"], label_visibility="collapsed")
    with col_btn2:
        skills_btn = st.button("Forecast", key="skills_btn")

    if skills_btn and skill_q.strip():
        with st.spinner(f"Analysing demand for '{skill_q}'..."):
            try:
                from skills_forecaster import forecast_skill
                report = forecast_skill(skill_q, sector, geography)

                st.markdown(f"""
                <div class="company-header">
                    <div class="company-name">{skill_q.title()}</div>
                    <div class="company-meta">{sector} · {geography} · Skills demand forecast</div>
                </div>
                """, unsafe_allow_html=True)

                demand_raw  = extract(report, "━━━ DEMAND SIGNALS ━━━",       ["━━━ MARKET",      "━━━ COMPETITOR"])
                market_raw  = extract(report, "━━━ MARKET CONTEXT ━━━",       ["━━━ COMPETITOR",  "━━━ UPGRAD"])
                comp_raw    = extract(report, "━━━ COMPETITOR COVERAGE ━━━",  ["━━━ UPGRAD",      "━━━ LEADING"])
                opp_raw     = extract(report, "━━━ UPGRAD OPPORTUNITY ━━━",   ["━━━ LEADING",     "━━━ FALSE"])
                news_raw_sk = extract(report, "━━━ LATEST NEWS & SIGNALS ━━━",["━━━ CONFIDENCE",  ""])

                stage   = parse_field(market_raw, "Current demand stage")
                ttm     = parse_field(market_raw, "Time to mainstream demand")
                action  = parse_field(opp_raw,    "Recommended action")
                urgency = parse_field(opp_raw,    "Urgency")
                growth  = parse_field(demand_raw, "Job posting growth (YoY)")

                urgency_badge = {
                    "High":   '<span class="threat-badge-high">● High urgency</span>',
                    "Medium": '<span class="threat-badge-med">● Medium urgency</span>',
                    "Low":    '<span class="threat-badge-low">● Low urgency</span>',
                }.get(urgency, "")

                st.markdown(f"""
                <div class="company-score-row">{urgency_badge}</div>
                <div class="stats-grid">
                    <div class="stat-cell"><div class="stat-label">Demand stage</div><div class="stat-value">{stage}</div></div>
                    <div class="stat-cell"><div class="stat-label">Job posting growth</div><div class="stat-value change-pos">{growth}</div></div>
                    <div class="stat-cell"><div class="stat-label">Time to mainstream</div><div class="stat-value">{ttm}</div></div>
                    <div class="stat-cell"><div class="stat-label">Recommendation</div><div class="stat-value">{action}</div></div>
                </div>
                """, unsafe_allow_html=True)

                col_d, col_o = st.columns(2)

                with col_d:
                    vol    = parse_field(demand_raw, "Job posting volume")
                    cos    = parse_field(demand_raw, "Top companies hiring for this skill")
                    salary = parse_field(demand_raw, "Average salary range")
                    gh     = parse_field(demand_raw, "GitHub / open source activity")
                    peak   = parse_field(market_raw, "Peak demand window")
                    adj    = parse_field(market_raw, "Adjacent skills in demand")

                    st.markdown(f"""
                    <div class="fin-section">
                        <div class="fin-section-title">Demand signals</div>
                        <table class="fin-table">
                            <tbody>
                                <tr><td>Job volume</td><td>{vol}</td></tr>
                                <tr><td>YoY growth</td><td class="change-pos">{growth}</td></tr>
                                <tr><td>Top hirers</td><td>{cos}</td></tr>
                                <tr><td>Salary range</td><td>{salary}</td></tr>
                                <tr><td>GitHub signal</td><td>{gh}</td></tr>
                                <tr><td>Peak window</td><td>{peak}</td></tr>
                                <tr><td>Adjacent skills</td><td>{adj}</td></tr>
                            </tbody>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                with col_o:
                    fmt     = parse_field(opp_raw,  "Suggested course format")
                    price   = parse_field(opp_raw,  "Suggested price range")
                    uni     = parse_field(opp_raw,  "Potential university partner")
                    est     = parse_field(opp_raw,  "Estimated course demand")
                    coursera= parse_field(comp_raw, "Coursera")
                    simpli  = parse_field(comp_raw, "Simplilearn")
                    gap     = parse_field(comp_raw, "Gap in market")

                    st.markdown(f"""
                    <div class="fin-section">
                        <div class="fin-section-title">upGrad opportunity</div>
                        <table class="fin-table">
                            <tbody>
                                <tr><td>Action</td><td><strong>{action}</strong></td></tr>
                                <tr><td>Course format</td><td>{fmt}</td></tr>
                                <tr><td>Price range</td><td>{price}</td></tr>
                                <tr><td>Uni partner</td><td>{uni}</td></tr>
                                <tr><td>Est. demand</td><td>{est}</td></tr>
                                <tr><td>Coursera</td><td>{coursera}</td></tr>
                                <tr><td>Simplilearn</td><td>{simpli}</td></tr>
                                <tr><td>Market gap</td><td>{gap}</td></tr>
                            </tbody>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('<div class="news-section-title">Latest signals & news</div>', unsafe_allow_html=True)
                news_html_sk = ""
                for line in [l.strip() for l in news_raw_sk.split("\n") if l.strip()][:5]:
                    parts    = line.split("—")
                    headline = parts[1].strip() if len(parts) > 1 else line
                    meta     = parts[0].strip() + " · " + parts[2].strip() if len(parts) > 2 else ""
                    news_html_sk += f"""
                    <div class="news-card">
                        <div class="news-dot"></div>
                        <div class="news-content">
                            <div class="news-headline">{make_links(headline)}</div>
                            <div class="news-meta">{make_links(meta)}</div>
                        </div>
                    </div>"""
                st.markdown(news_html_sk, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {str(e)[:200]}")

# ════════════════════════════════════════════════════════════════════
# TAB 3 — M&A INTELLIGENCE
# ════════════════════════════════════════════════════════════════════
with tab3:
    col_m, col_d, col_f, col_b3 = st.columns([3, 1.5, 1.5, 1])
    with col_m:
        ma_co = st.text_input("ma", placeholder="e.g. Masai School, Scaler, iNeuron", label_visibility="collapsed")
    with col_d:
        deal_type = st.selectbox("Deal", ["Acquisition", "Partnership", "Investment"], label_visibility="collapsed")
    with col_f:
        focus = st.selectbox("Focus", ["Content & curriculum", "Technology platform", "Geographic expansion", "User base acquisition", "B2B / Enterprise"], label_visibility="collapsed")
    with col_b3:
        ma_btn = st.button("Analyse", key="ma_btn")

    if ma_btn and ma_co.strip():
        with st.spinner(f"Running pre-diligence on {ma_co}..."):
            try:
                queries = [
                    f"{ma_co} edtech revenue EBITDA net loss FY25 FY24 India MCA filing crore",
                    f"{ma_co} funding investors valuation cap table 2025 2026",
                    f"{ma_co} acquisition merger upGrad deal partnership 2025 2026",
                    f"{ma_co} employees headcount app rating traffic 2026",
                    f"{ma_co} edtech news strategy expansion 2026",
                ]
                results = []
                for q in queries:
                    try:
                        r = tavily_client.search(q, search_depth="advanced", max_results=3)
                        for item in r.get("results", []):
                            results.append(f"SOURCE: {item.get('title')} ({item.get('url')})\n{item.get('content','')[:600]}")
                    except Exception:
                        pass

                search_text = "\n\n---\n\n".join(results)

                deal_focus_instructions = {
                    "Acquisition": "Focus on: financial health, burn rate, valuation, cap table, founder background, integration risk.",
                    "Partnership": "Focus on: content quality, brand reputation, audience overlap, revenue share potential.",
                    "Investment":  "Focus on: growth trajectory, market size, competitive moat, unit economics.",
                }.get(deal_type, "")

                focus_instructions = {
                    "Content & curriculum":    "Evaluate: course catalogue depth, faculty quality, university partnerships, content gaps.",
                    "Technology platform":     "Evaluate: tech stack, engineering headcount, product reviews, build vs buy analysis.",
                    "Geographic expansion":    "Evaluate: traffic by geography, language offerings, local regulatory presence.",
                    "User base acquisition":   "Evaluate: MAU, retention signals, demographic data, app ratings, learner overlap with upGrad.",
                    "B2B / Enterprise":        "Evaluate: enterprise client list, contract sizes, sales team headcount, B2B revenue share.",
                }.get(focus, "")

                ma_prompt = f"""
You are an M&A analyst at upGrad. Generate a pre-diligence brief for a potential {deal_type.lower()} of "{ma_co}".

DEAL TYPE INSTRUCTIONS: {deal_focus_instructions}
STRATEGIC FOCUS: {focus_instructions}

STRICT RULES:
- Only use data from search results below. Never invent financial figures.
- Tag every data point with source in brackets.
- If data unavailable, write "data unavailable".
- For every citation include the FULL URL: [Source Name](full_url)

SEARCH DATA:
{search_text}

OUTPUT FORMAT:

COMPANY: {ma_co}
DEAL TYPE: {deal_type} | FOCUS: {focus}

━━━ BUSINESS OVERVIEW ━━━
Business model:
Founded:
Headquarters:
Key verticals:

━━━ FINANCIALS ━━━
Revenue (FY25):
Revenue (FY24):
Net loss (FY25):
Total funding:
Last round:
Valuation:
Investors:
Confidence: [reason]

━━━ TRACTION ━━━
Monthly traffic:
App rating:
Headcount:
Headcount trend:

━━━ DEAL ASSESSMENT ━━━
Why this target for {deal_type.lower()}:
Synergies with upGrad:
Risks:
Integration complexity:
Red flags:

━━━ RECOMMENDATION ━━━
Overall: [Pursue / Evaluate further / Pass]
Rationale:
Next step:

━━━ CONFIDENCE SUMMARY ━━━
Data unavailable:
"""
                resp = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"You are a senior M&A analyst at upGrad. This is a {deal_type.lower()} evaluation focused on {focus}. Every financial claim must be cited. Flag missing data explicitly."},
                        {"role": "user",   "content": ma_prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.1
                )
                raw = resp.choices[0].message.content

                biz_raw  = extract(raw, "━━━ BUSINESS OVERVIEW ━━━", ["━━━ FINANCIALS"])
                fin_raw  = extract(raw, "━━━ FINANCIALS ━━━",        ["━━━ TRACTION"])
                tra_raw  = extract(raw, "━━━ TRACTION ━━━",          ["━━━ DEAL"])
                deal_raw = extract(raw, "━━━ DEAL ASSESSMENT ━━━",   ["━━━ RECOMMENDATION"])
                rec_raw  = extract(raw, "━━━ RECOMMENDATION ━━━",    ["━━━ CONFIDENCE"])

                rec = parse_field(rec_raw, "Overall")
                rec_badge = {
                    "Pursue":           '<span class="threat-badge-low">● Pursue</span>',
                    "Evaluate further": '<span class="threat-badge-med">● Evaluate further</span>',
                    "Pass":             '<span class="threat-badge-high">● Pass</span>',
                }.get(rec, f'<span class="threat-badge-med">● {rec}</span>')

                st.markdown(f"""
                <div class="company-header">
                    <div class="company-name">{ma_co.title()}</div>
                    <div class="company-meta">{deal_type} · {focus} · Pre-diligence brief</div>
                    <div class="company-score-row">{rec_badge}</div>
                    <div class="company-updated">Generated {today_str} · AI-assisted, analyst-verified</div>
                </div>
                """, unsafe_allow_html=True)

                rev = parse_field(fin_raw, "Revenue (FY25)")
                tf  = parse_field(fin_raw, "Total funding")
                tc  = parse_field(tra_raw, "Monthly traffic")
                hc  = parse_field(tra_raw, "Headcount")

                st.markdown(f"""
                <div class="stats-grid">
                    <div class="stat-cell"><div class="stat-label">Revenue FY25</div><div class="stat-value">{rev}</div></div>
                    <div class="stat-cell"><div class="stat-label">Total funding</div><div class="stat-value">{tf}</div></div>
                    <div class="stat-cell"><div class="stat-label">Monthly traffic</div><div class="stat-value">{tc}</div></div>
                    <div class="stat-cell"><div class="stat-label">Headcount</div><div class="stat-value">{hc}</div></div>
                </div>
                """, unsafe_allow_html=True)

                col_fl, col_fr = st.columns(2)

                with col_fl:
                    biz_model = parse_field(biz_raw, "Business model")
                    founded   = parse_field(biz_raw, "Founded")
                    hq        = parse_field(biz_raw, "Headquarters")
                    verticals = parse_field(biz_raw, "Key verticals")
                    rev24     = parse_field(fin_raw, "Revenue (FY24)")
                    loss      = parse_field(fin_raw, "Net loss (FY25)")
                    valuation = parse_field(fin_raw, "Valuation")
                    investors = parse_field(fin_raw, "Investors")

                    st.markdown(f"""
                    <div class="fin-section">
                        <div class="fin-section-title">Company & financials</div>
                        <table class="fin-table">
                            <tbody>
                                <tr><td>Business model</td><td>{biz_model}</td></tr>
                                <tr><td>Founded</td><td>{founded}</td></tr>
                                <tr><td>Headquarters</td><td>{hq}</td></tr>
                                <tr><td>Key verticals</td><td>{verticals}</td></tr>
                                <tr><td>Revenue FY24</td><td>{rev24}</td></tr>
                                <tr><td>Net loss FY25</td><td>{loss}</td></tr>
                                <tr><td>Valuation</td><td>{valuation}</td></tr>
                                <tr><td>Investors</td><td>{investors}</td></tr>
                            </tbody>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                with col_fr:
                    why       = parse_field(deal_raw, "Why this target")
                    syn       = parse_field(deal_raw, "Synergies with upGrad")
                    risks     = parse_field(deal_raw, "Risks")
                    integ     = parse_field(deal_raw, "Integration complexity")
                    red       = parse_field(deal_raw, "Red flags")
                    rationale = parse_field(rec_raw,  "Rationale")
                    next_s    = parse_field(rec_raw,  "Next step")

                    st.markdown(f"""
                    <div class="fin-section">
                        <div class="fin-section-title">Deal assessment — {deal_type}</div>
                        <table class="fin-table">
                            <tbody>
                                <tr><td>Why this target</td><td>{why}</td></tr>
                                <tr><td>Synergies</td><td>{syn}</td></tr>
                                <tr><td>Risks</td><td>{risks}</td></tr>
                                <tr><td>Integration</td><td>{integ}</td></tr>
                                <tr><td>Red flags</td><td>{red}</td></tr>
                                <tr><td>Rationale</td><td>{rationale}</td></tr>
                                <tr><td>Next step</td><td>{next_s}</td></tr>
                            </tbody>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {str(e)[:200]}")

# ════════════════════════════════════════════════════════════════════
# TAB 4 — CHAT
# ════════════════════════════════════════════════════════════════════
with tab4:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_msgs    = []

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin:0.5rem 0">
                <div style="background:#C0001A;color:white;padding:0.6rem 1rem;border-radius:12px 12px 2px 12px;max-width:75%;font-size:0.85rem">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;margin:0.5rem 0">
                <div style="background:#f8f9fa;border:1px solid #e0e0e0;padding:0.6rem 1rem;border-radius:12px 12px 12px 2px;max-width:85%;font-size:0.85rem;line-height:1.6">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#70757a;font-size:0.85rem">
            Ask anything about edtech competitors, M&A targets, or skills demand.<br>
            <span style="font-size:0.78rem">e.g. "Which edtech companies are gaining market share?" · "Is now a good time to launch an AI agents course?"</span>
        </div>""", unsafe_allow_html=True)

    col_ci, col_cs = st.columns([6, 1])
    with col_ci:
        user_input = st.text_input("chat", placeholder="Ask about competitors, skills, or M&A targets...", label_visibility="collapsed", key="chat_in")
    with col_cs:
        send_btn = st.button("Send", key="chat_send")

    if send_btn and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_msgs.append({"role": "user", "parts": [user_input]})

        try:
            search = tavily_client.search(
                user_input + " edtech India 2026",
                search_depth="advanced",
                max_results=4
            )
            context = "\n\n".join([
                f"{r.get('title')} ({r.get('url')})\n{r.get('content','')[:500]}"
                for r in search.get("results", [])
            ])

            history_text = ""
            for m in st.session_state.chat_msgs[:-1]:
                role = "User" if m["role"] == "user" else "Assistant"
                history_text += f"{role}: {m['parts'][0]}\n"

            resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an AI market intelligence analyst for upGrad. Answer concisely and cite sources. Frame all insights in terms of what they mean for upGrad specifically."},
                    {"role": "user",   "content": f"Search context:\n{context}\n\nConversation:\n{history_text}\nUser: {user_input}"}
                ],
                max_tokens=1500,
                temperature=0.2
            )

            ai_resp = resp.choices[0].message.content
            st.session_state.chat_history.append({"role": "ai",    "content": ai_resp})
            st.session_state.chat_msgs.append(   {"role": "model", "parts":   [ai_resp]})
            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)[:200]}")
