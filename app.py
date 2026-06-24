import streamlit as st
import sys
import re
from datetime import date

sys.path.append("/Users/dhruvpande/upgrad")

def make_links(text):
    if not text or text == "—":
        return text
    return re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" style="color:#C0001A;text-decoration:none">\1</a>',
        str(text)
    )

def is_empty(value):
    """True if a value should be treated as 'no data' and skipped from rendering."""
    if value is None:
        return True
    v = str(value).strip()
    return v == "" or v == "—" or v.lower() in ("data unavailable", "null", "none", "n/a", "nan")

def row(label, value, colspan=None, css_class=""):
    """Return a <tr> for a fin-table, or '' entirely if the value is empty."""
    if is_empty(value):
        return ""
    cls = f' class="{css_class}"' if css_class else ""
    if colspan:
        return f'<tr><td>{label}</td><td colspan="{colspan}"{cls}>{value}</td></tr>'
    return f'<tr><td>{label}</td><td{cls}>{value}</td></tr>'

def row4(label, v25, v24, v23, trend="", trend_cls=""):
    """4-column <tr> (metric, FY25, FY24, FY23, trend), or '' if every value is empty."""
    if is_empty(v25) and is_empty(v24) and is_empty(v23) and is_empty(trend):
        return ""
    c25 = v25 if not is_empty(v25) else '<span class="na">—</span>'
    c24 = v24 if not is_empty(v24) else '<span class="na">—</span>'
    c23 = v23 if not is_empty(v23) else '<span class="na">—</span>'
    ctrend = f'<td class="{trend_cls}">{trend}</td>' if not is_empty(trend) else '<td class="na">—</td>'
    return f'<tr><td>{label}</td><td>{c25}</td><td>{c24}</td><td>{c23}</td>{ctrend}</tr>'

def stat_cell(label, value):
    """One stats-grid cell, or '' if the value is empty."""
    if is_empty(value):
        return ""
    return f'<div class="stat-cell"><div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>'

def stats_grid(cells):
    """Build a stats-grid from stat_cell() outputs, sizing columns to however many survive."""
    cells = [c for c in cells if c]
    if not cells:
        return ""
    return (
        f'<div class="stats-grid" style="grid-template-columns:repeat({len(cells)},1fr)">'
        + "".join(cells) + "</div>"
    )

st.set_page_config(page_title="upGrad MIE", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .block-container { padding: 0 2rem 2rem; max-width: 1100px; margin: 0 auto; }
    .mie-nav { display: flex; align-items: center; gap: 2rem; padding: 0.8rem 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 1.5rem; }
    .mie-nav-logo { font-size: 1rem; font-weight: 500; color: #C0001A; }
    .mie-nav-link { font-size: 0.85rem; color: #444; }
    .company-name { font-size: 1.6rem; font-weight: 400; color: #202124; margin-bottom: 0.2rem; }
    .company-meta { font-size: 0.8rem; color: #70757a; margin-bottom: 1rem; }
    .company-score-row { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 0.5rem; }
    .company-updated { font-size: 0.75rem; color: #70757a; }
    .threat-badge-high { color: #c0392b; font-size: 0.85rem; font-weight: 500; background: #fce8e6; padding: 2px 10px; border-radius: 12px; }
    .threat-badge-med  { color: #e67e22; font-size: 0.85rem; font-weight: 500; background: #fef3e2; padding: 2px 10px; border-radius: 12px; }
    .threat-badge-low  { color: #27ae60; font-size: 0.85rem; font-weight: 500; background: #e6f4ea; padding: 2px 10px; border-radius: 12px; }
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; margin-bottom: 1.5rem; }
    .stat-cell { padding: 0.9rem 1rem; border-right: 1px solid #e0e0e0; }
    .stat-cell:last-child { border-right: none; }
    .stat-label { font-size: 0.72rem; color: #70757a; margin-bottom: 0.2rem; }
    .stat-value { font-size: 0.95rem; font-weight: 500; color: #202124; }
    .fin-section { margin-bottom: 1.5rem; }
    .fin-section-title { font-size: 1rem; font-weight: 500; color: #202124; margin-bottom: 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e0e0e0; }
    .fin-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .fin-table th { text-align: right; padding: 0.5rem 0.8rem; color: #70757a; font-weight: 400; border-bottom: 1px solid #e0e0e0; }
    .fin-table th:first-child { text-align: left; }
    .fin-table td { padding: 0.55rem 0.8rem; border-bottom: 1px solid #f1f3f4; color: #202124; text-align: right; }
    .fin-table td:first-child { text-align: left; color: #444; }
    .fin-table tr:hover td { background: #f8f9fa; }
    .change-pos { color: #1e8e3e; }
    .change-neg { color: #c0392b; }
    .na { color: #bbb; }
    .news-section-title { font-size: 1rem; font-weight: 500; color: #202124; margin-bottom: 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e0e0e0; }
    .news-card { display: flex; gap: 1rem; padding: 0.8rem 0; border-bottom: 1px solid #f1f3f4; align-items: flex-start; }
    .news-card:last-child { border-bottom: none; }
    .news-dot { width: 6px; height: 6px; border-radius: 50%; background: #C0001A; margin-top: 5px; flex-shrink: 0; }
    .news-content { flex: 1; }
    .news-headline { font-size: 0.85rem; color: #202124; font-weight: 500; margin-bottom: 0.2rem; line-height: 1.4; }
    .news-meta { font-size: 0.75rem; color: #70757a; }
    .news-relevance { font-size: 0.75rem; color: #444; margin-top: 0.2rem; font-style: italic; }
    .ai-verified { font-size: 0.72rem; color: #70757a; border: 1px solid #e0e0e0; padding: 2px 8px; border-radius: 12px; display: inline-block; }
    .source-tag { font-size: 0.7rem; color: #70757a; background: #f1f3f4; padding: 1px 5px; border-radius: 4px; }
    .watchlist-item { display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #f1f3f4; font-size: 0.82rem; }
    .watchlist-name { color: #202124; font-weight: 500; }
    .watchlist-meta { color: #70757a; font-size: 0.75rem; }
    .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #e0e0e0; gap: 0; }
    .stTabs [data-baseweb="tab"] { font-size: 0.85rem; padding: 0.6rem 1.2rem; color: #70757a; border-bottom: 2px solid transparent; margin-bottom: -2px; }
    .stTabs [aria-selected="true"] { color: #C0001A; border-bottom: 2px solid #C0001A; font-weight: 500; }
    div[data-testid="stTextInput"] input { border-radius: 24px; border: 1px solid #e0e0e0; padding: 0.5rem 1rem; font-size: 0.9rem; }
    div[data-testid="stTextInput"] input:focus { border-color: #C0001A; box-shadow: none; }
    .stButton > button { background: #C0001A; color: white; border: none; border-radius: 4px; font-size: 0.85rem; padding: 0.4rem 1.2rem; font-weight: 500; }
    .stButton > button:hover { background: #a30017; color: white; border: none; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mie-nav">
    <span class="mie-nav-logo">upGrad MIE</span>
    <span class="mie-nav-link">Company Briefs</span>
    <span class="mie-nav-link">Skills Demand</span>
    <span class="mie-nav-link">M&A Intel</span>
    <span class="mie-nav-link">Chat</span>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Company Briefs", "Skills Demand", "M&A Intelligence", "Chat"])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — COMPANY BRIEFS
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

    if search_btn and company_name.strip():
        from retrieval import get_company
        in_db = get_company(company_name)
        source_label = "Database" if in_db else "Live lookup"

        with st.spinner(f"Generating brief for {company_name}..."):
            try:
                from brief_generator import generate_brief
                raw = generate_brief(company_name)

                def extract(text, start_marker, end_markers):
                    try:
                        start = text.index(start_marker) + len(start_marker)
                        end = len(text)
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
                    if "declin" in v or "↓" in v: return "change-neg"
                    if "grow" in v or "increas" in v or "↑" in v: return "change-pos"
                    return ""

                financials_raw = extract(raw, "━━━ FINANCIALS ━━━",           ["━━━ LATEST", "━━━ TRACTION"])
                news_raw       = extract(raw, "━━━ LATEST NEWS",               ["━━━ TRACTION", "━━━ COMPETITIVE"])
                traction_raw   = extract(raw, "━━━ TRACTION ━━━",              ["━━━ COMPETITIVE", "━━━ KEY"])
                signals_raw    = extract(raw, "━━━ COMPETITIVE SIGNALS ━━━",   ["━━━ KEY", "━━━ PRIORITY"])
                takeaways_raw  = extract(raw, "━━━ KEY TAKEAWAYS",             ["━━━ PRIORITY", "━━━ CONFIDENCE"])
                priority_raw   = extract(raw, "━━━ PRIORITY SCORE ━━━",        ["━━━ CONFIDENCE", ""])

                threat = parse_field(priority_raw, "Overall threat level")
                threat_badge = {
                    "High":   '<span class="threat-badge-high">● High threat</span>',
                    "Medium": '<span class="threat-badge-med">● Medium threat</span>',
                    "Low":    '<span class="threat-badge-low">● Low threat</span>',
                }.get(threat, '<span class="threat-badge-med">● Analysed</span>')

                today_str = date.today().strftime("%d %b %Y")

                st.markdown(f"""
                <div>
                    <div class="company-name">{company_name.title()}</div>
                    <div class="company-meta">
                        Edtech · India &nbsp;·&nbsp;
                        <span class="ai-verified">AI-assisted, analyst-verified</span> &nbsp;·&nbsp;
                        <span class="source-tag">{source_label}</span>
                    </div>
                    <div class="company-score-row">{threat_badge}</div>
                    <div class="company-updated">Generated {today_str} · MCA, Entrackr, Tracxn, SimilarWeb, LinkedIn</div>
                </div>
                """, unsafe_allow_html=True)

                rev_fy25  = make_links(parse_field(financials_raw, "Revenue (FY25)"))
                rev_fy24  = make_links(parse_field(financials_raw, "Revenue (FY24)"))
                rev_fy23  = make_links(parse_field(financials_raw, "Revenue (FY23)"))
                ebitda    = make_links(parse_field(financials_raw, "EBITDA (FY25)"))
                traffic   = make_links(parse_field(traction_raw,   "Monthly web traffic"))
                funding   = make_links(parse_field(financials_raw, "Last funding round"))
                trend     = make_links(parse_field(financials_raw, "Revenue trend"))
                net25     = make_links(parse_field(financials_raw, "Net Income/Loss (FY25)"))
                net24     = make_links(parse_field(financials_raw, "Net Income/Loss (FY24)"))
                mktcap    = make_links(parse_field(financials_raw, "Market Cap"))
                total_f   = make_links(parse_field(financials_raw, "Total funding raised"))
                investors = make_links(parse_field(financials_raw, "Investor names"))
                headcount = make_links(parse_field(traction_raw,   "Headcount (current)"))
                app_and   = make_links(parse_field(traction_raw,   "App rating (Android)"))
                app_ios   = make_links(parse_field(traction_raw,   "App rating (iOS)"))
                hc_trend  = make_links(parse_field(traction_raw,   "Headcount trend"))
                t_trend   = make_links(parse_field(traction_raw,   "Traffic trend (MoM)"))
                reviews   = make_links(parse_field(traction_raw,   "Total app reviews"))
                hiring    = make_links(parse_field(signals_raw,    "Hiring signals"))
                geo       = make_links(parse_field(signals_raw,    "Geographic expansion signals"))
                b2b       = make_links(parse_field(signals_raw,    "B2B / enterprise moves"))
                mkt       = make_links(parse_field(signals_raw,    "Marketing spend signals"))

                # ── Stock data (listed companies only) ──
                from stock_data import get_stock_data, format_price, format_mktcap
                from ticker_lookup import lookup_ticker
                # Check DB for ticker first, then fall back to dynamic NSE lookup —
                # no more hand-maintaining a dict every time a company IPOs.
                if in_db and isinstance(in_db, dict) and in_db.get("stock_ticker"):
                    ticker = in_db["stock_ticker"]
                else:
                    ticker = lookup_ticker(company_name)
                stock  = get_stock_data(ticker) if ticker else None

                if stock:
                    change_color = "#1e8e3e" if (stock["change_pct"] or 0) >= 0 else "#c0392b"
                    change_arrow = "▲" if (stock["change_pct"] or 0) >= 0 else "▼"
                    prices = stock["prices_24h"]
                    times  = stock["times_24h"]
                    chart_svg = ""
                    if prices and len(prices) > 1:
                        mn, mx = min(prices), max(prices)
                        rng = mx - mn if mx != mn else 1
                        pad = rng * 0.1
                        mn, mx = mn - pad, mx + pad
                        rng = mx - mn

                        w, h = 320, 110
                        pad_l, pad_b, pad_t = 56, 20, 10
                        plot_w = w - pad_l - 8
                        plot_h = h - pad_b - pad_t

                        pts = " ".join([
                            f"{pad_l + (i/(len(prices)-1))*plot_w:.1f},{pad_t + (1-((p-mn)/rng))*plot_h:.1f}"
                            for i, p in enumerate(prices)
                        ])
                        spark_color = "#1e8e3e" if prices[-1] >= prices[0] else "#c0392b"

                        # y-axis: 3 horizontal gridlines with price labels
                        y_ticks = [mn + rng * f for f in (0, 0.5, 1)]
                        y_gridlines = ""
                        for yt in y_ticks:
                            y_pos = pad_t + (1 - ((yt - mn) / rng)) * plot_h
                            y_gridlines += (
                                f'<line x1="{pad_l}" y1="{y_pos:.1f}" x2="{w-8}" y2="{y_pos:.1f}" '
                                f'stroke="#eceff1" stroke-width="1"/>'
                                f'<text x="{pad_l-6}" y="{y_pos+3:.1f}" font-size="9" fill="#70757a" '
                                f'text-anchor="end">{yt:,.0f}</text>'
                            )

                        # x-axis: first, middle, last time labels
                        x_idxs = [0, len(times)//2, len(times)-1]
                        x_labels = ""
                        for xi in x_idxs:
                            x_pos = pad_l + (xi/(len(prices)-1))*plot_w
                            x_labels += (
                                f'<text x="{x_pos:.1f}" y="{h-4}" font-size="9" fill="#70757a" '
                                f'text-anchor="middle">{times[xi]}</text>'
                            )

                        chart_svg = (
                            f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                            f'{y_gridlines}'
                            f'<polyline points="{pts}" fill="none" stroke="{spark_color}" stroke-width="1.5" stroke-linejoin="round"/>'
                            f'{x_labels}'
                            f'</svg>'
                        )
                    st.markdown(f"""
                    <div style="border:1px solid #e0e0e0;border-radius:8px;padding:0.9rem 1.2rem;margin-bottom:1.2rem;display:flex;align-items:center;justify-content:space-between;background:#fff">
                        <div>
                            <div style="font-size:0.72rem;color:#70757a;margin-bottom:0.2rem">{stock['ticker']} · {stock['as_of']}</div>
                            <div style="font-size:1.4rem;font-weight:400;color:#202124">{format_price(stock['price'])}</div>
                            <div style="font-size:0.82rem;color:{change_color};margin-top:0.1rem">
                                {change_arrow} ₹{abs(stock['change'] or 0):.2f} ({abs(stock['change_pct'] or 0):.2f}%)
                            </div>
                        </div>
                        <div style="text-align:center">
                            {chart_svg}
                            <div style="font-size:0.7rem;color:#70757a;margin-top:2px">Last 24 hours</div>
                        </div>
                        <div style="text-align:right">
                            <div style="font-size:0.72rem;color:#70757a">Market cap</div>
                            <div style="font-size:0.88rem;font-weight:500;color:#202124">{format_mktcap(stock['mktcap_cr'])}</div>
                            <div style="font-size:0.72rem;color:#70757a;margin-top:0.4rem">52W range</div>
                            <div style="font-size:0.82rem;color:#202124">{format_price(stock['low_52w'])} – {format_price(stock['high_52w'])}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(stats_grid([
                    stat_cell("Revenue FY25", rev_fy25),
                    stat_cell("EBITDA FY25", ebitda),
                    stat_cell("Monthly traffic", traffic),
                    stat_cell("Last funding", funding),
                ]), unsafe_allow_html=True)

                sub_ov, sub_fin, sub_sig, sub_news_tab = st.tabs(["Overview", "Financials", "Signals", "News"])

                with sub_ov:
                    takeaway_lines = [l.strip() for l in takeaways_raw.split("\n") if l.strip() and l.strip()[0].isdigit()]
                    glance_text = takeaway_lines[0].split(":", 1)[-1].strip() if takeaway_lines else "No summary available."
                    st.markdown(f"""
                    <div style="background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1.2rem">
                        <div style="font-size:0.75rem;color:#70757a;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem">At a glance — AI summary</div>
                        <div style="font-size:0.85rem;color:#202124;line-height:1.6">{make_links(glance_text)}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    labels = ["Immediate threat", "Opportunity", "Action this week", "Watch (30 days)"]
                    takeaway_rows = ""
                    for i, line in enumerate(takeaway_lines[:4]):
                        content = make_links(line.split(".", 1)[-1].strip() if "." in line else line)
                        content = content.split(":", 1)[-1].strip() if ":" in content else content
                        if is_empty(content):
                            continue
                        label = labels[i] if i < len(labels) else f"Point {i+1}"
                        takeaway_rows += f"<tr><td style='width:160px;color:#70757a'>{label}</td><td>{content}</td></tr>"
                    if takeaway_rows:
                        st.markdown(f"""
                        <div class="fin-section">
                            <div class="fin-section-title">Key takeaways for upGrad</div>
                            <table class="fin-table"><tbody>{takeaway_rows}</tbody></table>
                        </div>
                        """, unsafe_allow_html=True)

                with sub_fin:
                    fin_rows = "".join([
                        row4("Revenue", rev_fy25, rev_fy24, rev_fy23, trend, trend_class(trend)),
                        row("EBITDA", ebitda),
                        row("Net Income / Loss", net25 if not is_empty(net25) else net24),
                        row("Market Cap", mktcap, colspan=3),
                        row("Total funding", total_f, colspan=3),
                        row("Key investors", investors, colspan=4),
                    ])
                    if fin_rows:
                        st.markdown(f"""
                        <div class="fin-section">
                            <div class="fin-section-title">Financials</div>
                            <table class="fin-table">
                                <thead>
                                    <tr><th>Metric</th><th>FY25</th><th>FY24</th><th>FY23</th><th>Trend</th></tr>
                                </thead>
                                <tbody>{fin_rows}</tbody>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="color:#70757a;font-size:0.85rem">No financial data available.</div>', unsafe_allow_html=True)

                with sub_sig:
                    col_t, col_s = st.columns(2)
                    with col_t:
                        traction_rows = "".join([
                            row("Monthly traffic", traffic),
                            row("Traffic trend", t_trend, css_class=trend_class(t_trend)),
                            row("App rating (Android)", app_and),
                            row("App rating (iOS)", app_ios),
                            row("Total reviews", reviews),
                            row("Headcount", headcount),
                            row("Headcount trend", hc_trend),
                        ])
                        if traction_rows:
                            st.markdown(f"""
                            <div class="fin-section">
                                <div class="fin-section-title">Traction</div>
                                <table class="fin-table">
                                    <tbody>{traction_rows}</tbody>
                                </table>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color:#70757a;font-size:0.85rem">No traction data available.</div>', unsafe_allow_html=True)
                    with col_s:
                        signal_rows = "".join([
                            row("Hiring signals", hiring),
                            row("Geo expansion", geo),
                            row("B2B / enterprise", b2b),
                            row("Marketing signals", mkt),
                        ])
                        if signal_rows:
                            st.markdown(f"""
                            <div class="fin-section">
                                <div class="fin-section-title">Competitive signals</div>
                                <table class="fin-table">
                                    <tbody>{signal_rows}</tbody>
                                </table>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color:#70757a;font-size:0.85rem">No competitive signals available.</div>', unsafe_allow_html=True)

                with sub_news_tab:
                    st.markdown('<div class="news-section-title">Latest news & signals</div>', unsafe_allow_html=True)
                    news_lines = [l.strip() for l in news_raw.split("\n") if l.strip() and not l.strip().startswith("[")]
                    news_html = ""
                    for line in news_lines[:6]:
                        parts = line.split("—")
                        if len(parts) >= 3:
                            date_str = parts[0].strip()
                            headline = make_links(parts[1].strip())
                            source   = make_links(parts[2].strip())
                            relevance= parts[3].strip() if len(parts) > 3 else ""
                            news_html += f"""
                            <div class="news-card">
                                <div class="news-dot"></div>
                                <div class="news-content">
                                    <div class="news-headline">{headline}</div>
                                    <div class="news-meta">{date_str} · {source}</div>
                                    <div class="news-relevance">{relevance}</div>
                                </div>
                            </div>"""
                        else:
                            news_html += f"""
                            <div class="news-card">
                                <div class="news-dot"></div>
                                <div class="news-content">
                                    <div class="news-headline">{make_links(line)}</div>
                                </div>
                            </div>"""
                    if news_html:
                        st.markdown(news_html, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="color:#70757a;font-size:0.85rem">No recent news found.</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Something went wrong: {str(e)[:120]}")

    else:
        st.markdown('<div class="fin-section-title" style="margin-top:1rem">Tracked companies</div>', unsafe_allow_html=True)
        try:
            from retrieval import get_all_companies
            companies = get_all_companies()
            if companies:
                for c in companies[:15]:
                    name = c.get('name', '')
                    rev  = c.get('revenue_fy24', '—')
                    tier = c.get('tier', '')
                    tier_label = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}.get(tier, "")
                    rev_display = f"Rev FY24: ₹{rev} Cr" if not is_empty(rev) else ""
                    st.markdown(f"""
                    <div class="watchlist-item">
                        <div><span class="watchlist-name">{name}</span> &nbsp;<span class="source-tag">{tier_label}</span></div>
                        <div class="watchlist-meta">{rev_display}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#70757a;font-size:0.85rem">No companies in database yet.</div>', unsafe_allow_html=True)
        except Exception as e:
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

                def sk_field(block, label):
                    for line in block.split("\n"):
                        if line.strip().startswith(label):
                            val = line.split(":", 1)[-1].strip()
                            return val if val else "—"
                    return "—"

                def sk_section(text, marker, end_markers):
                    try:
                        start = text.index(marker) + len(marker)
                        end = len(text)
                        for m in end_markers:
                            try:
                                pos = text.index(m, start)
                                if pos < end: end = pos
                            except: pass
                        return text[start:end].strip()
                    except: return ""

                demand_raw  = sk_section(report, "━━━ DEMAND SIGNALS ━━━",        ["━━━ MARKET",      "━━━ COMPETITOR"])
                market_raw  = sk_section(report, "━━━ MARKET CONTEXT ━━━",        ["━━━ COMPETITOR",  "━━━ UPGRAD"])
                comp_raw    = sk_section(report, "━━━ COMPETITOR COVERAGE ━━━",   ["━━━ UPGRAD",      "━━━ LEADING"])
                opp_raw     = sk_section(report, "━━━ UPGRAD OPPORTUNITY ━━━",    ["━━━ LEADING",     "━━━ FALSE"])
                news_raw_sk = sk_section(report, "━━━ LATEST NEWS & SIGNALS ━━━", ["━━━ CONFIDENCE",  ""])

                stage   = sk_field(market_raw, "Current demand stage")
                ttm     = sk_field(market_raw, "Time to mainstream demand")
                action  = sk_field(opp_raw,    "Recommended action")
                urgency = sk_field(opp_raw,    "Urgency")
                growth  = sk_field(demand_raw, "Job posting growth (YoY)")

                urgency_badge = {
                    "High":   '<span class="threat-badge-high">● High urgency</span>',
                    "Medium": '<span class="threat-badge-med">● Medium urgency</span>',
                    "Low":    '<span class="threat-badge-low">● Low urgency</span>',
                }.get(urgency, "")

                st.markdown(f"""
                <div>
                    <div class="company-name">{skill_q.title()}</div>
                    <div class="company-meta">{sector} · {geography} · Skills demand forecast</div>
                    <div class="company-score-row">{urgency_badge}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(stats_grid([
                    stat_cell("Demand stage", stage),
                    stat_cell("Job growth (YoY)", growth),
                    stat_cell("Time to mainstream", ttm),
                    stat_cell("Recommendation", action),
                ]), unsafe_allow_html=True)

                col_d, col_o = st.columns(2)

                with col_d:
                    vol    = make_links(sk_field(demand_raw, "Job posting volume"))
                    cos    = make_links(sk_field(demand_raw, "Top companies hiring"))
                    salary = make_links(sk_field(demand_raw, "Average salary range"))
                    gh     = make_links(sk_field(demand_raw, "GitHub / open source activity"))
                    peak   = make_links(sk_field(market_raw, "Peak demand window"))
                    adj    = make_links(sk_field(market_raw, "Adjacent skills in demand"))

                    demand_rows = "".join([
                        row("Job volume", vol),
                        row("YoY growth", growth, css_class="change-pos"),
                        row("Top hirers", cos),
                        row("Salary range", salary),
                        row("GitHub signal", gh),
                        row("Peak window", peak),
                        row("Adjacent skills", adj),
                    ])
                    if demand_rows:
                        st.markdown(f"""
                        <div class="fin-section">
                            <div class="fin-section-title">Demand signals</div>
                            <table class="fin-table">
                                <tbody>{demand_rows}</tbody>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="color:#70757a;font-size:0.85rem">No demand signal data available.</div>', unsafe_allow_html=True)

                with col_o:
                    fmt      = make_links(sk_field(opp_raw,  "Suggested course format"))
                    price    = make_links(sk_field(opp_raw,  "Suggested price range"))
                    uni      = make_links(sk_field(opp_raw,  "Potential university partner"))
                    est      = make_links(sk_field(opp_raw,  "Estimated course demand"))
                    coursera = make_links(sk_field(comp_raw, "Coursera"))
                    simpli   = make_links(sk_field(comp_raw, "Simplilearn"))
                    gap      = make_links(sk_field(comp_raw, "Gap in market"))

                    opp_rows = "".join([
                        row("Action", f"<strong>{action}</strong>") if not is_empty(action) else "",
                        row("Course format", fmt),
                        row("Price range", price),
                        row("Uni partner", uni),
                        row("Est. demand", est),
                        row("Coursera", coursera),
                        row("Simplilearn", simpli),
                        row("Market gap", gap),
                    ])
                    if opp_rows:
                        st.markdown(f"""
                        <div class="fin-section">
                            <div class="fin-section-title">upGrad opportunity</div>
                            <table class="fin-table">
                                <tbody>{opp_rows}</tbody>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="color:#70757a;font-size:0.85rem">No opportunity data available.</div>', unsafe_allow_html=True)

                st.markdown('<div class="news-section-title">Latest signals & news</div>', unsafe_allow_html=True)
                sk_news_html = ""
                for line in [l.strip() for l in news_raw_sk.split("\n") if l.strip()][:5]:
                    parts = line.split("—")
                    headline = make_links(parts[1].strip()) if len(parts) > 1 else make_links(line)
                    meta     = parts[0].strip() + " · " + make_links(parts[2].strip()) if len(parts) > 2 else ""
                    if is_empty(headline):
                        continue
                    sk_news_html += f"""
                    <div class="news-card">
                        <div class="news-dot"></div>
                        <div class="news-content">
                            <div class="news-headline">{headline}</div>
                            <div class="news-meta">{meta}</div>
                        </div>
                    </div>"""
                if sk_news_html:
                    st.markdown(sk_news_html, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="color:#70757a;font-size:0.85rem">No recent signals found.</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {str(e)[:120]}")

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
                from tavily import TavilyClient
                from groq import Groq
                import os
                from dotenv import load_dotenv
                load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

                tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                groq   = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
                        r = tavily.search(q, search_depth="advanced", max_results=3)
                        for item in r.get("results", []):
                            results.append(f"SOURCE: {item.get('title')} ({item.get('url')})\n{item.get('content','')[:500]}")
                    except: pass

                search_text = "\n\n---\n\n".join(results)

                deal_focus_instructions = {
                    "Acquisition": "Focus on: financial health, burn rate, valuation, cap table, founder background, integration risk, what upGrad gets by owning this company outright.",
                    "Partnership": "Focus on: content quality, brand reputation, audience overlap, what unique capability this company brings, revenue share potential.",
                    "Investment":  "Focus on: growth trajectory, market size, competitive moat, unit economics, whether a minority stake makes strategic sense for upGrad."
                }.get(deal_type, "")

                focus_instructions = {
                    "Content & curriculum":    "Evaluate: course catalogue depth, faculty quality, university partnerships, content gaps upGrad has.",
                    "Technology platform":     "Evaluate: tech stack, engineering headcount, product reviews, API capabilities, build vs buy.",
                    "Geographic expansion":    "Evaluate: traffic by geography, language offerings, local regulatory presence, regional partnerships.",
                    "User base acquisition":   "Evaluate: MAU, retention signals, demographic data, app ratings, review sentiment, learner overlap.",
                    "B2B / Enterprise":        "Evaluate: enterprise client list, contract sizes, sales team headcount, B2B revenue share."
                }.get(focus, "")

                ma_prompt = f"""
You are an M&A analyst at upGrad. Generate a pre-diligence brief for a potential {deal_type.lower()} of "{ma_co}".

DEAL TYPE: {deal_focus_instructions}
STRATEGIC FOCUS: {focus_instructions}

STRICT RULES:
- Only use data from search results. Never invent figures.
- Every citation: [Source Name](full_url)
- If unavailable: "data unavailable"

SEARCH DATA:
{search_text}

OUTPUT:

COMPANY: {ma_co}

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

                resp = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Senior M&A analyst at upGrad. {deal_type} evaluation focused on {focus}. Cite every claim. Flag missing data."},
                        {"role": "user", "content": ma_prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.1
                )
                raw = resp.choices[0].message.content

                def ma_sec(text, marker, ends):
                    try:
                        s = text.index(marker) + len(marker)
                        e = len(text)
                        for m in ends:
                            try:
                                p = text.index(m, s)
                                if p < e: e = p
                            except: pass
                        return text[s:e].strip()
                    except: return ""

                def ma_f(block, label):
                    for line in block.split("\n"):
                        if line.strip().startswith(label):
                            v = line.split(":", 1)[-1].strip()
                            return v if v else "—"
                    return "—"

                biz_raw  = ma_sec(raw, "━━━ BUSINESS OVERVIEW ━━━", ["━━━ FINANCIALS"])
                fin_raw  = ma_sec(raw, "━━━ FINANCIALS ━━━",        ["━━━ TRACTION"])
                tra_raw  = ma_sec(raw, "━━━ TRACTION ━━━",          ["━━━ DEAL"])
                deal_raw = ma_sec(raw, "━━━ DEAL ASSESSMENT ━━━",   ["━━━ RECOMMENDATION"])
                rec_raw  = ma_sec(raw, "━━━ RECOMMENDATION ━━━",    ["━━━ CONFIDENCE"])

                rec = ma_f(rec_raw, "Overall")
                rec_badge = {
                    "Pursue":           '<span class="threat-badge-low">● Pursue</span>',
                    "Evaluate further": '<span class="threat-badge-med">● Evaluate further</span>',
                    "Pass":             '<span class="threat-badge-high">● Pass</span>',
                }.get(rec, f'<span class="threat-badge-med">● {rec}</span>')

                st.markdown(f"""
                <div>
                    <div class="company-name">{ma_co.title()}</div>
                    <div class="company-meta">{deal_type} · {focus} · Pre-diligence brief</div>
                    <div class="company-score-row">{rec_badge}</div>
                    <div class="company-updated">Generated {date.today().strftime('%d %b %Y')} · AI-assisted, analyst-verified</div>
                </div>
                """, unsafe_allow_html=True)

                rev  = make_links(ma_f(fin_raw, "Revenue (FY25)"))
                tf   = make_links(ma_f(fin_raw, "Total funding"))
                tc   = make_links(ma_f(tra_raw, "Monthly traffic"))
                hc   = make_links(ma_f(tra_raw, "Headcount"))

                st.markdown(stats_grid([
                    stat_cell("Revenue FY25", rev),
                    stat_cell("Total funding", tf),
                    stat_cell("Monthly traffic", tc),
                    stat_cell("Headcount", hc),
                ]), unsafe_allow_html=True)

                col_fl, col_fr = st.columns(2)

                with col_fl:
                    biz_rows = "".join([
                        row("Business model", make_links(ma_f(biz_raw, "Business model"))),
                        row("Founded", ma_f(biz_raw, "Founded")),
                        row("Headquarters", ma_f(biz_raw, "Headquarters")),
                        row("Key verticals", make_links(ma_f(biz_raw, "Key verticals"))),
                        row("Revenue FY24", make_links(ma_f(fin_raw, "Revenue (FY24)"))),
                        row("Net loss FY25", make_links(ma_f(fin_raw, "Net loss (FY25)"))),
                        row("Valuation", make_links(ma_f(fin_raw, "Valuation"))),
                        row("Investors", make_links(ma_f(fin_raw, "Investors"))),
                    ])
                    if biz_rows:
                        st.markdown(f"""
                        <div class="fin-section">
                            <div class="fin-section-title">Company & financials</div>
                            <table class="fin-table">
                                <tbody>{biz_rows}</tbody>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="color:#70757a;font-size:0.85rem">No company/financial data available.</div>', unsafe_allow_html=True)

                with col_fr:
                    deal_rows = "".join([
                        row("Why this target", make_links(ma_f(deal_raw, "Why this target"))),
                        row("Synergies", make_links(ma_f(deal_raw, "Synergies"))),
                        row("Risks", make_links(ma_f(deal_raw, "Risks"))),
                        row("Integration", make_links(ma_f(deal_raw, "Integration complexity"))),
                        row("Red flags", make_links(ma_f(deal_raw, "Red flags"))),
                        row("Rationale", make_links(ma_f(rec_raw, "Rationale"))),
                        row("Next step", make_links(ma_f(rec_raw, "Next step"))),
                    ])
                    if deal_rows:
                        st.markdown(f"""
                        <div class="fin-section">
                            <div class="fin-section-title">Deal assessment — {deal_type}</div>
                            <table class="fin-table">
                                <tbody>{deal_rows}</tbody>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="color:#70757a;font-size:0.85rem">No deal assessment data available.</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {str(e)[:120]}")

# ════════════════════════════════════════════════════════════════════
# TAB 4 — CHAT
# ════════════════════════════════════════════════════════════════════
with tab4:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_msgs = []

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
            from tavily import TavilyClient
            from groq import Groq
            import os
            from dotenv import load_dotenv
            load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

            tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            groq   = Groq(api_key=os.getenv("GROQ_API_KEY"))

            search  = tavily.search(user_input + " edtech India 2026", search_depth="advanced", max_results=4)
            context = "\n\n".join([f"{r.get('title')} ({r.get('url')})\n{r.get('content','')[:500]}" for r in search.get("results", [])])

            history_text = ""
            for m in st.session_state.chat_msgs[:-1]:
                role = "User" if m["role"] == "user" else "Assistant"
                history_text += f"{role}: {m['parts'][0]}\n"

            resp = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an AI market intelligence analyst for upGrad. Answer concisely and cite sources with URLs. Frame all insights in terms of what they mean for upGrad."},
                    {"role": "user", "content": f"Search context:\n{context}\n\nConversation:\n{history_text}\nUser: {user_input}"}
                ],
                max_tokens=1500,
                temperature=0.2
            )

            ai_resp = resp.choices[0].message.content
            st.session_state.chat_history.append({"role": "ai", "content": ai_resp})
            st.session_state.chat_msgs.append({"role": "model", "parts": [ai_resp]})
            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)[:100]}")