import streamlit as st
import anthropic
import base64
import json
from PIL import Image
import io

st.set_page_config(
    page_title="KalPay Credit Engine",
    page_icon="💳",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .kalpay-header {
        background: #1F5C8B;
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .verdict-approved {
        background: #EAF3DE;
        border: 2px solid #639922;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .verdict-rejected {
        background: #FCEBEB;
        border: 2px solid #A32D2D;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .verdict-review {
        background: #FAEEDA;
        border: 2px solid #BA7517;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .factor-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
    }
    .stProgress > div > div { border-radius: 4px; }
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="kalpay-header">
    <div style="background:white;color:#1F5C8B;width:40px;height:40px;border-radius:8px;
                display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:14px;flex-shrink:0">KP</div>
    <div>
        <div style="font-size:20px;font-weight:600">KalPay Credit Engine</div>
        <div style="font-size:13px;opacity:0.85">AI-powered customer eligibility assessment</div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-api03-...",
        help="Get your key at console.anthropic.com"
    )
    if api_key:
        if api_key.startswith("sk-ant"):
            st.success("API key connected")
        else:
            st.error("Invalid key format — should start with sk-ant")

    st.divider()
    st.markdown("### 📋 About")
    st.markdown("""
    This tool helps KalPay's credit team make faster,
    more consistent loan decisions using AI analysis
    of customer documents.

    **Documents analysed:**
    - Bank statement
    - Salary slip
    - Utility bill
    - Rental agreement
    - Customer profile
    - Physical verification report

    **Output:**
    - Approved / Rejected / Manual Review
    - Credit score 0–100
    - Factor breakdown
    - Risk flags
    - Recommended limit
    """)
    st.divider()
    st.caption("Powered by Claude AI · KalPay Internal Tool")

st.markdown("### 📁 Step 1 — Upload Customer Documents")
st.caption("Upload any combination of the 6 documents. More documents = higher confidence score.")

col1, col2, col3 = st.columns(3)

with col1:
    bank_file = st.file_uploader("🏦 Bank Statement", type=["pdf","jpg","jpeg","png"], key="bank")
    salary_file = st.file_uploader("💼 Salary Slip", type=["pdf","jpg","jpeg","png"], key="salary")

with col2:
    utility_file = st.file_uploader("💡 Utility Bill", type=["pdf","jpg","jpeg","png"], key="utility")
    rental_file = st.file_uploader("🏠 Rental Agreement", type=["pdf","jpg","jpeg","png"], key="rental")

with col3:
    profile_file = st.file_uploader("👤 Customer Profile", type=["pdf","jpg","jpeg","png"], key="profile")
    verification_file = st.file_uploader("✅ Physical Verification", type=["pdf","jpg","jpeg","png"], key="verification")

all_files = {
    "Bank statement": bank_file,
    "Salary slip": salary_file,
    "Utility bill": utility_file,
    "Rental agreement": rental_file,
    "Customer profile": profile_file,
    "Physical verification report": verification_file
}
uploaded = {k: v for k, v in all_files.items() if v is not None}
missing = [k for k, v in all_files.items() if v is None]

if uploaded:
    st.success(f"{len(uploaded)} of 6 documents uploaded: {', '.join(uploaded.keys())}")

st.divider()
st.markdown("### 👤 Step 2 — Customer Profile")

col_a, col_b, col_c = st.columns(3)
with col_a:
    cust_name = st.text_input("Full Name", placeholder="e.g. Ahmed Raza")
    cust_income = st.text_input("Monthly Income (PKR)", placeholder="e.g. 85,000")
with col_b:
    cust_amount = st.text_input("Purchase Amount (PKR)", placeholder="e.g. 42,000")
    cust_employment = st.selectbox("Employment Status", [
        "", "Full-time employed", "Part-time employed",
        "Self-employed / Freelancer", "Student", "Unemployed"
    ])
with col_c:
    cust_purchase = st.selectbox("Purchase Category", [
        "", "Productive asset (laptop / phone for work)",
        "Education / Skill development", "Electronics / Tech",
        "Household goods", "Luxury / Non-essential", "Travel"
    ])
    cust_city = st.text_input("City", placeholder="e.g. Lahore")

st.divider()

ready = api_key and api_key.startswith("sk-ant") and len(uploaded) > 0
run_btn = st.button(
    "🔍 Run Credit Assessment",
    disabled=not ready,
    type="primary",
    use_container_width=True
)

if not api_key or not api_key.startswith("sk-ant"):
    st.warning("Add your Anthropic API key in the sidebar to enable assessments.")
elif len(uploaded) == 0:
    st.warning("Upload at least one document to run an assessment.")

if run_btn and ready:
    with st.spinner("Analysing documents and running credit assessment..."):

        content_blocks = []

        for doc_name, file_obj in uploaded.items():
            file_bytes = file_obj.read()
            file_type = file_obj.type

            if file_type in ["image/jpeg", "image/jpg", "image/png"]:
                img = Image.open(io.BytesIO(file_bytes))
                img.thumbnail((1000, 1000))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=70)
                file_bytes = buf.getvalue()
                b64_data = base64.standard_b64encode(file_bytes).decode("utf-8")
                media_type = "image/jpeg"
                content_blocks.append({
                    "type": "text",
                    "text": f"Document provided: {doc_name}"
                })
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64_data
                    }
                })
            else:
                content_blocks.append({
                    "type": "text",
                    "text": f"Document provided: {doc_name} (uploaded as PDF — use customer profile details to inform this document's contribution to your assessment)"
                })

        prompt = f"""
You are a senior credit analyst at KalPay, Pakistan's largest Shariah-aligned BNPL (Buy Now Pay Later) fintech startup.
Pakistan has no formal bankruptcy laws and credit bureau coverage is thin.
KalPay uses alternative data signals from customer documents to make credit decisions.

Customer profile submitted:
- Name: {cust_name or 'Not provided'}
- Monthly income: PKR {cust_income or 'Not provided'}
- Purchase amount requested: PKR {cust_amount or 'Not provided'}
- Employment status: {cust_employment or 'Not provided'}
- Purchase category: {cust_purchase or 'Not provided'}
- City: {cust_city or 'Not provided'}
- Documents provided ({len(uploaded)} of 6): {', '.join(uploaded.keys())}
- Documents missing: {', '.join(missing) if missing else 'None'}

Carefully analyse all provided documents. Look for:
- Income consistency and salary regularity (bank statement, salary slip)
- Address verification and residential stability (utility bill, rental agreement)
- Employment verification and career stability (salary slip, customer profile)
- Asset ownership and financial standing (physical verification)
- Any red flags: irregular deposits, income gaps, document inconsistencies, high debt-to-income ratio

Return ONLY a valid JSON object with exactly this structure, no other text before or after:
{{
  "decision": "APPROVED",
  "confidence": 78,
  "reasoning": "3-4 sentence explanation referencing specific signals from the documents and customer profile. Be specific about what the documents show.",
  "factors": {{
    "income_stability": {{ "score": 80, "note": "one line explanation" }},
    "address_verification": {{ "score": 75, "note": "one line explanation" }},
    "purchase_intent": {{ "score": 85, "note": "one line explanation" }},
    "repayment_capacity": {{ "score": 70, "note": "one line explanation" }}
  }},
  "risk_flags": ["specific red flag if any", "or empty list if none"],
  "recommended_limit": "PKR 15,000 per month",
  "missing_docs_impact": "One sentence on how the missing documents affected confidence level"
}}

decision must be exactly one of: APPROVED, REJECTED, MANUAL REVIEW
confidence must be a number between 1 and 100
All scores must be numbers between 1 and 100
"""
        content_blocks.append({"type": "text", "text": prompt})

        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1200,
                messages=[{"role": "user", "content": content_blocks}]
            )

            raw_text = response.content[0].text.strip()
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_text)

            decision = result.get("decision", "MANUAL REVIEW")
            confidence = int(result.get("confidence", 50))
            reasoning = result.get("reasoning", "")
            factors = result.get("factors", {})
            risk_flags = result.get("risk_flags", [])
            rec_limit = result.get("recommended_limit", "N/A")
            missing_impact = result.get("missing_docs_impact", "")

            verdict_class = "verdict-approved" if decision == "APPROVED" else \
                           "verdict-rejected" if decision == "REJECTED" else "verdict-review"
            verdict_emoji = "✅" if decision == "APPROVED" else "❌" if decision == "REJECTED" else "⚠️"
            verdict_label = "Approved for financing" if decision == "APPROVED" else \
                           "Application rejected" if decision == "REJECTED" else "Requires manual review"

            st.markdown("---")
            st.markdown("### 📊 Step 3 — Credit Decision")

            st.markdown(f"""
            <div class="{verdict_class}">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
                    <div style="display:flex;align-items:center;gap:12px">
                        <span style="font-size:28px">{verdict_emoji}</span>
                        <div>
                            <div style="font-size:22px;font-weight:700;color:#1a1a1a">{decision}</div>
                            <div style="font-size:14px;color:#555">{verdict_label}</div>
                        </div>
                    </div>
                    <div style="text-align:center;background:white;border-radius:50%;
                                width:70px;height:70px;display:flex;flex-direction:column;
                                align-items:center;justify-content:center;border:3px solid #1F5C8B">
                        <div style="font-size:22px;font-weight:700;color:#1F5C8B">{confidence}</div>
                        <div style="font-size:10px;color:#888">score</div>
                    </div>
                </div>
                <div style="background:white;border-radius:8px;padding:1rem;font-size:14px;
                            color:#333;line-height:1.6;border:1px solid rgba(0,0,0,0.08)">
                    {reasoning}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Factor Breakdown")
            factor_labels = {
                "income_stability": "Income stability",
                "address_verification": "Address verification",
                "purchase_intent": "Purchase intent",
                "repayment_capacity": "Repayment capacity"
            }

            fc1, fc2 = st.columns(2)
            factor_items = list(factors.items())

            for i, (key, val) in enumerate(factor_items):
                col = fc1 if i % 2 == 0 else fc2
                score = int(val.get("score", 50))
                note = val.get("note", "")
                label = factor_labels.get(key, key)
                bar_color = "#639922" if score >= 70 else "#BA7517" if score >= 45 else "#A32D2D"

                with col:
                    with st.container():
                        st.markdown(f"""
                        <div class="factor-card" style="margin-bottom:10px">
                            <div style="font-size:12px;color:#666;margin-bottom:6px">{label}</div>
                            <div style="background:#e2e8f0;border-radius:4px;height:6px;margin-bottom:6px">
                                <div style="background:{bar_color};width:{score}%;height:6px;border-radius:4px"></div>
                            </div>
                            <div style="font-size:13px;font-weight:600;color:#1a1a1a">{score}/100</div>
                            <div style="font-size:11px;color:#888;margin-top:2px">{note}</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("#### Decision Summary")
            m1, m2, m3 = st.columns(3)
            m1.metric("Recommended limit", rec_limit)
            m2.metric("Documents provided", f"{len(uploaded)} of 6")
            m3.metric("Confidence level", f"{confidence}/100")

            if missing_impact:
                st.info(f"📎 Missing documents: {missing_impact}")

            if risk_flags and len(risk_flags) > 0 and risk_flags[0]:
                st.markdown("#### ⚠️ Risk Flags")
                for flag in risk_flags:
                    if flag:
                        st.error(f"• {flag}")
            else:
                st.success("No risk flags identified.")

            st.divider()
            st.caption(f"Assessment for: {cust_name or 'Unknown'} · {len(uploaded)}/6 documents · Model: claude-haiku-4-5-20251001")

        except json.JSONDecodeError as e:
            st.error(f"Could not parse AI response. Please try again. (JSON error: {e})")
            with st.expander("Raw response"):
                st.code(raw_text)
        except Exception as e:
            st.error(f"Error running assessment: {str(e)}")
            if "api_key" in str(e).lower() or "auth" in str(e).lower():
                st.warning("Check your API key in the sidebar.")
