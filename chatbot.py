"""
chatbot.py — PostBot AI Brain
Using Groq API (FREE — 14,400 requests/day, no credit card needed)
Model: Llama 3.3 70B (best free model available)

Get your free key at: https://console.groq.com
Key format: gsk_...
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads GROQ_API_KEY from .env silently

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def _get_client():
    """Get Groq client using key from .env file."""
    key = os.getenv("GROQ_API_KEY", "").strip()

    if not key:
        return None, (
            "❌ GROQ_API_KEY not found in .env file.\n\n"
            "Steps to fix:\n"
            "1. Go to console.groq.com → Sign up free\n"
            "2. Click API Keys → Create API Key\n"
            "3. Open your .env file and add:\n"
            "   GROQ_API_KEY=gsk_your_key_here"
        )

    if not GROQ_AVAILABLE:
        return None, (
            "❌ groq package not installed.\n"
            "Run in CMD: pip install groq"
        )

    try:
        client = Groq(api_key=key)
        return client, None
    except Exception as e:
        return None, f"❌ Groq connection error: {e}"


def build_system_prompt(officer: dict, district_info: dict, suggestion: dict) -> str:
    """Build the full context prompt for Groq / Llama."""
    from model_utils import get_tier

    d        = district_info
    s        = suggestion
    tier     = get_tier(d['district_delivery_rate'])
    rate_pct = round(d['district_delivery_rate'] * 100, 2)
    bo_pct   = round(d['bo_ratio'] * 100, 2)
    exp_rate = round(s['expected_rate'] * 100, 2)

    return f"""You are PostBot — the official AI assistant for India Post's District Infrastructure Efficiency System.
You are helping {officer['name']} ({officer['role']}, {officer['circle']} Circle), Officer ID: {officer['id']}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABOUT THIS SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This system is built on a CatBoost machine learning model (R² = 0.9243) trained on 
1,65,000+ India Post offices across 754 districts. It predicts district delivery 
performance and suggests infrastructure improvements.

KEY FACTS (always cite these in your answers):
• Branch Offices (BO)   → deliver 98.7% of mail — the MOST efficient type
• Sub Post Offices (PO) → deliver only 76.2%    — 1 in 4 has NO active delivery
• Head Offices (HO)     → deliver 99.1%          — very reliable but very few
• BO Ratio is the #1 delivery predictor (Pearson r = +0.87 with delivery rate)
• Districts with BO ratio above 85% consistently achieve delivery rates above 95%

4 PERFORMANCE TIERS (from K-Means clustering of 720 districts):
  🟢 High Performance     (205 districts) → avg 98.6% delivery, BO ratio 90.5%
  🔵 Good Performance     (261 districts) → avg 96.2% delivery, BO ratio 86.1%
  🟡 Moderate Performance (235 districts) → avg 94.5% delivery, BO ratio 83.0%
  🔴 Low Performance       (19 districts) → avg 39.7% delivery, BO ratio 15.9%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT DISTRICT — REAL DATA FROM DATASET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
District          : {d['district'].title()}
State             : {d['statename'].title()}
Branch Offices    : {d['bo_count']}  (98.7% delivery — most efficient)
Sub Post Offices  : {d['po_count']}  (76.2% delivery — lowest efficiency)
Head Offices      : {d['ho_count']}  (99.1% delivery — most reliable)
Total Offices     : {d['total_offices']}
Current Delivery Rate : {rate_pct}%
Current BO Ratio      : {bo_pct}%  (target: above 85%)
Performance Tier      : {tier['emoji']} {tier['label']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODEL RECOMMENDATION FOR THIS DISTRICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Branch Offices to add : {s['bo_to_add']}
Expected new rate     : {exp_rate}%
Expected improvement  : +{s['improvement']} percentage points
Next tier target      : {s['next_tier']['label'] if s['next_tier'] else 'Already at top tier'}
Inactive POs to activate : {s['po_to_activate']} (approx)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR BEHAVIOUR AS POSTBOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Use SIMPLE language. The officer is a postal administrator, not a data scientist.
- Always reference the SPECIFIC numbers from the district data above.
- For what-if questions, use this formula:
    new_rate = (delivery_offices + 0.987 × added_BOs) / (total_offices + added_BOs)
    where delivery_offices = {round(d['district_delivery_rate'] * d['total_offices'])}
- Always show BEFORE → AFTER when doing calculations.
- Be professional, concise, and helpful.
- Do NOT ask the officer for information already provided above.
- Format your response clearly with bullet points or numbered steps where helpful.
"""


def ask_postbot(question: str, officer: dict,
                district_info: dict, suggestion: dict,
                chat_history: list) -> str:
    """
    Send a question to Groq Llama 3.3 70B and return the answer.
    Includes automatic fallback if API fails.
    """
    client, err = _get_client()
    if err:
        return err

    system_prompt = build_system_prompt(officer, district_info, suggestion)

    # Build conversation history for context
    messages = [{"role": "system", "content": system_prompt}]

    # Add last 6 messages of history for context (keep prompt short)
    recent = chat_history[-6:] if len(chat_history) > 6 else chat_history
    for msg in recent:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})

    # Add current question
    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Best free model on Groq
            messages=messages,
            max_tokens=1024,
            temperature=0.4,    # Slightly creative but mostly factual
        )
        return response.choices[0].message.content

    except Exception as e:
        err_str = str(e).lower()

        if "rate_limit" in err_str or "rate limit" in err_str:
            return (
                "⚠️ **Rate limit reached temporarily.**\n\n"
                "Groq allows 30 requests per minute. Please wait 60 seconds and try again.\n\n"
                "*(Your daily limit of 14,400 requests has NOT been used up — "
                "this is just a per-minute limit.)*"
            )

        if "invalid api key" in err_str or "unauthorized" in err_str or "401" in err_str:
            return (
                "❌ **Invalid Groq API Key.**\n\n"
                "Steps to fix:\n"
                "1. Go to **console.groq.com**\n"
                "2. Click **API Keys** → **Create API Key**\n"
                "3. Open your `.env` file and update:\n"
                "   `GROQ_API_KEY=gsk_your_new_key_here`\n"
                "4. Restart the app with `streamlit run app.py`"
            )

        if "quota" in err_str or "exceeded" in err_str:
            return (
                "⚠️ **Daily quota exceeded.**\n\n"
                "Your daily limit of 14,400 free requests on Groq has been reached.\n\n"
                "Options:\n"
                "• Wait until tomorrow (quota resets daily)\n"
                "• Create a new free account at **console.groq.com**\n"
                "• The pre-calculated analysis on screen is still accurate and available."
            )

        return f"⚠️ Groq API error: {e}\n\nPlease try again in a moment."


def test_api_key() -> tuple:
    """Test if the Groq API key in .env is working. Returns (bool, message)."""
    client, err = _get_client()
    if err:
        return False, err
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Reply with exactly: POSTBOT_READY"}],
            max_tokens=10
        )
        return True, "✅ Groq API connected. Llama 3.3 70B ready."
    except Exception as e:
        return False, f"❌ {e}"
