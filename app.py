import streamlit as st
import sys
sys.path.append("/Users/dhruvpande/upgrad")

st.set_page_config(
    page_title="upGrad MIE",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding: 2rem 2.5rem; }
    
    .header-bar {
        background: #C0001A;
        padding: 1.2rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .header-bar h1 { color: white; margin: 0; font-size: 1.6rem; font-weight: 700; }
    .header-bar p { color: rgba(255,255,255,0.8); margin: 0.2rem 0 0; font-size: 0.88rem; }
    
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .metric-card h3 { color: #C0001A; font-size: 1.6rem; margin: 0; font-weight: 700; }
    .metric-card p { color: #6c757d; font-size: 0.8rem; margin: 0.2rem 0 0; }

    .status-db {
        background: #d1e7dd; color: #0f5132;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        font-size: 0.8rem; font-weight: 500; display: inline-block;
    }
    .status-live {
        background: #cfe2ff; color: #084298;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        font-size: 0.8rem; font-weight: 500; display: inline-block;
    }
    .coming-soon {
        background: #f8f9fa; border: 1px dashed #dee2e6;
        border-radius: 10px; padding: 3rem;
        text-align: center; color: #adb5bd;
    }

    .stButton > button {
        background: #C0001A; color: white;
        border: none; border-radius: 7px;
        font-weight: 600; width: 100%;
    }
    .stButton > button:hover { background: #a30017; color: white; border: none; }

    .chat-msg-user {
        background: #C0001A; color: white;
        padding: 0.7rem 1rem; border-radius: 10px 10px 2px 10px;
        margin: 0.5rem 0; max-width: 75%; margin-left: auto;
        font-size: 0.9rem;
    }
    .chat-msg-ai {
        background: white; color: #212529;
        padding: 0.7rem 1rem; border-radius: 10px 10px 10px 2px;
        margin: 0.5rem 0; max-width: 85%;
        border: 1px solid #e9ecef; font-size: 0.9rem;
        line-height: 1.6;
    }
    .chat-container {
        background: #f8f9fa; border-radius: 10px;
        padding: 1rem; min-height: 300px;
        max-height: 450px; overflow-y: auto;
        border: 1px solid #e9ecef;
    }

    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---- HEADER ----
st.markdown("""
<div class="header-bar">
    <h1>upGrad Market Intelligence Engine</h1>
    <p>Competitive intelligence · M&A research · Skills forecasting</p>
</div>
""", unsafe_allow_html=True)

# ---- METRICS ----
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="metric-card"><h3>100</h3><p>Companies in database</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card"><h3>3</h3><p>Intelligence modules</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card"><h3>&lt;2m</h3><p>Brief generation</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><h3>Live</h3><p>Unknown company lookup</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---- TABS ----
tab1, tab2, tab3, tab4 = st.tabs([
    "Company Briefs",
    "Skills Demand",
    "M&A Intelligence",
    "Chat"
])

# ================================================================
# TAB 1: COMPANY BRIEFS
# ================================================================
with tab1:
    st.markdown("#### Generate Company Intelligence Brief")
    st.caption("Known companies pull from our database. Unknown companies trigger a live AI-powered lookup.")

    col_i, col_b = st.columns([4, 1])
    with col_i:
        company_name = st.text_input(
            "company",
            placeholder="e.g. Simplilearn, Unacademy, BYJU'S",
            label_visibility="collapsed"
        )
    with col_b:
        generate = st.button("Generate", key="gen_brief")

    if generate:
        if not company_name.strip():
            st.warning("Please enter a company name.")
        else:
            from retrieval import get_company
            in_db = get_company(company_name)

            if in_db:
                st.markdown('<span class="status-db">✓ Found in database</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-live">⚡ Live lookup</span>', unsafe_allow_html=True)

            with st.spinner(f"Researching {company_name}..."):
                try:
                    from brief_generator import generate_brief
                    brief = generate_brief(company_name)
                    st.markdown("<br>", unsafe_allow_html=True)

                    # Display each section cleanly
                    for section in brief.split("\n\n"):
                        if not section.strip():
                            continue
                        lines = section.strip().split("\n")
                        header = lines[0]
                        if any(header.startswith(x) for x in [
                            "COMPANY", "FINANCIALS", "TRACTION",
                            "SIGNALS", "KEY TAKEAWAYS", "CONFIDENCE"
                        ]):
                            st.markdown(f"**{header}**")
                            for line in lines[1:]:
                                if line.strip():
                                    st.markdown(f"{line}")
                        else:
                            for line in lines:
                                if line.strip():
                                    st.markdown(line)
                        st.divider()

                except Exception as e:
                    st.error(f"API temporarily unavailable. Try again in a few minutes.")

# ================================================================
# TAB 2: SKILLS DEMAND
# ================================================================
with tab2:
    st.markdown("#### Skills Demand Forecaster")
    st.caption("Identify emerging skills 6–12 months before they become mainstream course demand.")

    skill_query = st.text_input(
        "skill",
        placeholder="e.g. Agentic AI, Cloud FinOps, Healthcare Data",
        label_visibility="collapsed"
    )
    col_s1, col_s2 = st.columns([2, 2])
    with col_s1:
        sector = st.selectbox("Sector", ["Technology", "Healthcare", "Finance", "Manufacturing", "All"])
    with col_s2:
        geography = st.selectbox("Geography", ["India", "Southeast Asia", "Global", "MENA"])

    if st.button("Forecast Demand", key="skills_btn"):
        if not skill_query.strip():
            st.warning("Enter a skill or topic to forecast.")
        else:
            with st.spinner(f"Analysing demand signals for '{skill_query}'..."):
                try:
                    from google import genai
                    from google.genai import types
                    import os
                    from dotenv import load_dotenv
                    load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

                    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

                    skills_prompt = f"""
You are a skills demand forecaster for an Indian edtech company called upGrad.

Analyse demand signals for the skill/topic: "{skill_query}"
Sector: {sector}
Geography: {geography}

Search the web for current signals and return a structured forecast.

OUTPUT FORMAT (follow exactly):

SKILL: {skill_query}
SECTOR: {sector} | GEOGRAPHY: {geography}

DEMAND SIGNALS
Job posting volume:
Job posting growth (YoY):
Top hiring companies:
GitHub/open source activity:
Industry reports:

FORECAST
Current demand stage: [Emerging / Growing / Mainstream / Declining]
Time to mainstream: [X months estimate]
Confidence: [High/Medium/Low]
Peak demand window:

UPGRAD OPPORTUNITY
Current upGrad coverage:
Gap assessment:
Recommended action: [Launch now / Plan for next quarter / Monitor]
Estimated course demand:

LEADING INDICATORS
[List 3 signals that predict this skill will grow]

FALSE POSITIVE RISKS
[List any reasons this signal might not translate to course demand]

SOURCES
[Cite every data point with source and date]
"""
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=skills_prompt,
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearch())]
                        )
                    )

                    for section in response.text.split("\n\n"):
                        if not section.strip():
                            continue
                        lines = section.strip().split("\n")
                        if lines[0].isupper() or lines[0].startswith("SKILL"):
                            st.markdown(f"**{lines[0]}**")
                            for line in lines[1:]:
                                if line.strip():
                                    st.markdown(line)
                        else:
                            for line in lines:
                                if line.strip():
                                    st.markdown(line)
                        st.divider()

                except Exception as e:
                    st.error("API temporarily unavailable. Try again in a few minutes.")

# ================================================================
# TAB 3: M&A INTELLIGENCE
# ================================================================
with tab3:
    st.markdown("#### M&A Target Intelligence")
    st.caption("Generate a pre-diligence brief for any acquisition or partnership target.")

    ma_company = st.text_input(
        "ma_company",
        placeholder="e.g. Masai School, Scaler, iNeuron",
        label_visibility="collapsed"
    )
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        deal_type = st.selectbox("Deal type", ["Acquisition", "Partnership", "Investment"])
    with col_m2:
        strategic_focus = st.selectbox("Strategic focus", [
            "Content & curriculum", "Technology platform",
            "Geographic expansion", "User base acquisition", "B2B / Enterprise"
        ])

    if st.button("Generate M&A Brief", key="ma_btn"):
        if not ma_company.strip():
            st.warning("Enter a company name.")
        else:
            with st.spinner(f"Running pre-diligence on {ma_company}..."):
                try:
                    from google import genai
                    from google.genai import types
                    import os
                    from dotenv import load_dotenv
                    load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

                    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

                    ma_prompt = f"""
You are an M&A analyst at upGrad, an Indian edtech company.

Generate a pre-diligence brief for a potential {deal_type.lower()} of "{ma_company}".
Strategic focus: {strategic_focus}

STRICT RULES:
- Only use data you can find and cite. Never estimate financial figures without a source.
- Label every data point with its source in brackets.
- If data is unavailable, write "data unavailable" — never guess.
- Flag confidence as High / Medium / Low per section.

OUTPUT FORMAT:

COMPANY: {ma_company}
DEAL TYPE: {deal_type} | FOCUS: {strategic_focus}

BUSINESS OVERVIEW
Business model:
Founded:
Headquarters:
Key products/verticals:

FINANCIALS
Revenue (latest FY):
Net loss (latest FY):
Revenue trend:
Last funding round:
Total funding raised:
Valuation (last known):
Confidence: [reason]

TRACTION
Monthly active users:
Monthly web traffic:
App rating:
Headcount:
Headcount trend:
Confidence: [reason]

STRATEGIC FIT FOR UPGRAD
Why this target:
Synergies:
Risks:
Integration complexity:

DEAL CONSIDERATIONS
Recommended structure:
Key due diligence areas:
Red flags:
Overall recommendation: [Pursue / Evaluate further / Pass]

CONFIDENCE SUMMARY
[Fields where data was unavailable]

SOURCES
[All citations with dates]
"""
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=ma_prompt,
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearch())]
                        )
                    )

                    for section in response.text.split("\n\n"):
                        if not section.strip():
                            continue
                        lines = section.strip().split("\n")
                        if lines[0].isupper() or lines[0].startswith("COMPANY") or lines[0].startswith("DEAL"):
                            st.markdown(f"**{lines[0]}**")
                            for line in lines[1:]:
                                if line.strip():
                                    st.markdown(line)
                        else:
                            for line in lines:
                                if line.strip():
                                    st.markdown(line)
                        st.divider()

                except Exception as e:
                    st.error("API temporarily unavailable. Try again in a few minutes.")

# ================================================================
# TAB 4: CHAT
# ================================================================
with tab4:
    st.markdown("#### Intelligence Chat")
    st.caption("Ask anything about competitors, skills, markets, or M&A targets. The AI searches live and answers with citations.")

    # Init chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_messages = []

    # Display chat
    chat_html = '<div class="chat-container">'
    if not st.session_state.chat_history:
        chat_html += '<p style="color:#adb5bd;text-align:center;margin-top:2rem">Ask anything — e.g. "Which edtech companies are gaining market share?" or "What skills will be in demand in healthcare in 2026?"</p>'
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            chat_html += f'<div class="chat-msg-user">{msg["content"]}</div>'
        else:
            chat_html += f'<div class="chat-msg-ai">{msg["content"]}</div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chat, col_send = st.columns([5, 1])
    with col_chat:
        user_input = st.text_input(
            "chat_input",
            placeholder="Ask a question about the edtech market...",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col_send:
        send = st.button("Send", key="chat_send")

    if send and user_input.strip():
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        st.session_state.chat_messages.append({
            "role": "user",
            "parts": [user_input]
        })

        with st.spinner("Thinking..."):
            try:
                from google import genai
                from google.genai import types
                import os
                from dotenv import load_dotenv
                load_dotenv("/Users/dhruvpande/upgrad/.env", override=True)

                gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

                system_context = """You are an AI market intelligence analyst for upGrad, 
an Indian edtech company. You help the strategy team with competitive intelligence, 
M&A research, and skills demand forecasting. 

Always:
- Search for current data before answering
- Cite your sources with dates
- Be concise and actionable
- Frame insights in terms of what they mean for upGrad specifically
- Flag confidence level for any data point"""

                full_prompt = system_context + "\n\nConversation so far:\n"
                for msg in st.session_state.chat_messages[:-1]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    full_prompt += f"{role}: {msg['parts'][0]}\n"
                full_prompt += f"User: {user_input}"

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )

                ai_response = response.text
                st.session_state.chat_history.append({
                    "role": "ai",
                    "content": ai_response
                })
                st.session_state.chat_messages.append({
                    "role": "model",
                    "parts": [ai_response]
                })
                st.rerun()

            except Exception as e:
                st.error("API temporarily unavailable. Try again in a few minutes.")

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("### upGrad MIE")
    st.markdown("---")
    st.markdown("**Modules**")
    st.markdown("Company Briefs")
    st.markdown("Skills Demand")
    st.markdown(" M&A Intelligence")
    st.markdown("Chat")
    st.markdown("---")

    try:
        from retrieval import get_all_companies
        companies = get_all_companies()
        st.metric("Companies in DB", len(companies))
        if companies:
            st.markdown("**Recent:**")
            for c in companies[-5:]:
                st.markdown(f"• {c['name']}")
    except:
        st.caption("Loading...")

    st.markdown("---")
    st.caption("v0.1 · Built by Dhruv Pande")