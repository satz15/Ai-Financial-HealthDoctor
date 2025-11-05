# from openai import OpenAI
# from app.config import settings

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# def analyze_financial_statement(summary):
#     income = float(summary.get("total_income", 0))
#     expenses = float(summary.get("total_expenses", 0))
#     transactions = int(summary.get("transactions_count", 0))

#     savings = float(max(income - expenses, 0))
#     debt_to_income = float(round((expenses / income) * 100, 2)) if income else 0.0
#     savings_rate = float(round((savings / income) * 100, 2)) if income else 0.0

#     prompt = f"""
#     You are an AI financial advisor.
#     Analyze this financial data:
#     - Total Income: ₹{income}
#     - Total Expenses: ₹{expenses}
#     - Savings: ₹{savings}
#     - Transactions: {transactions}
#     - Debt-to-Income: {debt_to_income}%
#     - Savings Rate: {savings_rate}%

#     Provide:
#     1. Summary
#     2. Strengths
#     3. Top 3 personalized recommendations
#     4. Overall Financial Fitness Score
#     """

#     try:
#         ai_response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7
#         )
#         ai_text = ai_response.choices[0].message.content
#     except Exception as e:
#         ai_text = f"AI analysis unavailable ({e})"

#     return {
#         "Total Income": income,
#         "Total Expenses": expenses,
#         "Savings": savings,
#         "Debt-to-Income (%)": debt_to_income,
#         "Savings Rate (%)": savings_rate,
#         "AI Financial Insights": ai_text
#     }

from openai import OpenAI
from app.config import settings
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def clean_text(text: str) -> str:
    """Remove markdown and clean spacing."""
    if not text:
        return ""
    text = re.sub(r"[*#`_]+", "", text)
    text = re.sub(r"([a-z])to([A-Z])", r"\1-to-\2", text)
    text = re.sub(r"\.{2,}", ".", text)
    return re.sub(r"\s+", " ", text).strip()

def split_to_list(text: str):
    """Convert AI paragraphs or bullets into clean list format."""
    if not text:
        return []
    text = re.sub(r"[*•#]+", "-", text)
    parts = [clean_text(p.strip("- ")) for p in text.split("\n") if p.strip()]
    if len(parts) == 1 and "." in parts[0]:
        parts = [s.strip() + "." for s in re.split(r"\.\s+", parts[0]) if s.strip()]
    return parts

def analyze_financial_statement(summary):
    income = float(summary.get("total_income", 0))
    expenses = float(summary.get("total_expenses", 0))
    transactions = int(summary.get("transactions_count", 0))
    savings = float(max(income - expenses, 0))
    debt_ratio = round((expenses / income) * 100, 2) if income else 0.0
    savings_rate = round((savings / income) * 100, 2) if income else 0.0

    # 🔥 Improved AI prompt (prevents repetition)
    prompt = f"""
    You are a professional financial advisor.
    Below is a user's financial data:
    - Total Income: ₹{income}
    - Total Expenses: ₹{expenses}
    - Total Savings: ₹{savings}
    - Debt-to-Income Ratio: {debt_ratio}%
    - Savings Rate: {savings_rate}%
    - Transactions: {transactions}

    Task:
    Analyze this data and create a professional, concise financial health report.
    DO NOT restate or repeat the above numbers directly. Instead, interpret them to explain performance and insights.

    Structure your response clearly in this format:

    ### Summary
    - 3 short bullet points summarizing the user's financial health overall (good/average/poor).

    ### Strengths
    - 3 bullet points about what is going well financially.

    ### Areas to Improve
    - 3 bullet points about what needs attention.

    ### Strategies
    **Debt Management**
    - Dynamic recommendations based on the debt ratio.
    **Savings Strategy**
    - Personalized advice based on the savings rate.
    **Investment Strategy**
    - Suggestions based on financial stability and savings.

    ### Financial Fitness Score
    - Give a 1–10 score with a one-line reason.
    """

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a structured, concise financial analyst who interprets data, not repeats it."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw = res.choices[0].message.content.strip()

        def extract(title):
            match = re.search(rf"### {title}\n([\s\S]*?)(?=\n###|\Z)", raw)
            return match.group(1).strip() if match else ""

        # Clean extracted content
        summary_text = split_to_list(extract("Summary"))
        strengths_text = split_to_list(extract("Strengths"))
        improve_text = split_to_list(extract("Areas to Improve"))
        strategies_text = clean_text(extract("Strategies"))
        score_text = clean_text(extract("Financial Fitness Score"))

        return {
            "Financial_Overview": {
                "Total Income (₹)": round(income, 2),
                "Total Expenses (₹)": round(expenses, 2),
                "Savings (₹)": round(savings, 2),
                "Debt-to-Income (%)": debt_ratio,
                "Savings Rate (%)": savings_rate,
            },
            "AI_Financial_Analysis": {
                "Summary": summary_text,
                "Strengths": strengths_text,
                "Areas_to_Improve": improve_text,
                "Strategies": strategies_text,
                "Financial_Fitness_Score": score_text
            },
        }

    except Exception as e:
        return {"error": f"AI analysis unavailable ({e})"}

