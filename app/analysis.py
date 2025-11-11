from groq import Groq
import os, re, math
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[*#`_]+", "", text)
    return re.sub(r"\s+", " ", text).strip()

def split_to_list(text: str):
    if not text:
        return []
    parts = [clean_text(p.strip("- ")) for p in text.split("\n") if p.strip()]
    if len(parts) == 1 and "." in parts[0]:
        parts = [s.strip() + "." for s in re.split(r"\.\s+", parts[0]) if s.strip()]
    return parts

    income = float(summary.get("total_income", 0))
    expenses = float(summary.get("total_expenses", 0))
    transactions = int(summary.get("transactions_count", 0))
    savings = max(income - expenses, 0)
    debt_ratio = round((expenses / income) * 100, 2) if income else 0.0
    savings_rate = round((savings / income) * 100, 2) if income else 0.0

    # 🧠 AI Prompt
    prompt = f"""
    You are a professional financial coach.
    Analyze the user's financial health:
    - Income: ₹{income}
    - Expenses: ₹{expenses}
    - Savings: ₹{savings}
    - Debt-to-Income Ratio: {debt_ratio}%
    - Savings Rate: {savings_rate}%
    - Transactions: {transactions}

    1️⃣ Create a section **Spending Reallocation & Reward Plan**
    - Suggest 3–4 specific expense categories the user could reduce (Food, Entertainment, Shopping, etc.)
    - For each, show:
      "Reduce [category] by ₹amount → invest monthly → could grow to ₹X in 3 years (at 10% annual return)."
    - Keep tone friendly and goal-oriented.

    2️⃣ Create a section **Goal-Based Financial Plan**
    - Suggest how the user can plan goals like Emergency Fund, Car, House, or Travel
    - For each goal, estimate how much per month they should save and how long it will take.

    3️⃣ Add regular financial sections:
    ### Summary
    ### Strengths
    ### Areas to Improve
    ### Strategies
    ### Financial Fitness Score (1–10 with reason)
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert AI financial advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    raw = res.choices[0].message.content.strip()

    def extract(title):
        match = re.search(rf"### {title}\n([\s\S]*?)(?=\n###|\Z)", raw)
        return match.group(1).strip() if match else ""

    # 🧮 Auto reward simulation (simple projection)
    reward_plan = [
        {
            "category": "Dining Out",
            "cut": 1500,
            "potential": future_value(1500, 10, 3)
        },
        {
            "category": "Streaming Services",
            "cut": 800,
            "potential": future_value(800, 10, 3)
        },
        {
            "category": "Online Shopping",
            "cut": 2000,
            "potential": future_value(2000, 10, 3)
        }
    ]

    # 🎯 Auto goal planner (based on income)
    goals_plan = {
        "Emergency Fund": {
            "target": round(income * 3, 2),
            "monthly_saving": round(income * 0.15, 2),
            "months_to_reach": round((income * 3) / (income * 0.15))
        },
        "Dream Car": {
            "target": 500000,
            "monthly_saving": round(income * 0.25, 2),
            "months_to_reach": round(500000 / (income * 0.25))
        }
    }

    return {
        "Financial_Overview": {
            "Total Income (₹)": round(income, 2),
            "Total Expenses (₹)": round(expenses, 2),
            "Savings (₹)": round(savings, 2),
            "Debt-to-Income (%)": debt_ratio,
            "Savings Rate (%)": savings_rate,
        },
        "AI_Financial_Analysis": {
            "Summary": split_to_list(extract("Summary")),
            "Strengths": split_to_list(extract("Strengths")),
            "Areas_to_Improve": split_to_list(extract("Areas to Improve")),
            "Strategies": split_to_list(extract("Strategies")),
            "Financial_Fitness_Score": clean_text(extract("Financial Fitness Score")),
        },
        "Spending_Reallocation": reward_plan,
        "Goal_Based_Plan": goals_plan,
    }

def future_value(monthly_investment, annual_rate, years):
    """Simple compound interest projection with monthly compounding."""
    r = annual_rate / 100 / 12
    n = years * 12
    return round(monthly_investment * (((1 + r) ** n - 1) / r), 2)


def analyze_financial_statement(summary, transactions_df=None):
    income = float(summary.get("total_income", 0))
    expenses = float(summary.get("total_expenses", 0))
    transactions = int(summary.get("transactions_count", 0))
    savings = max(income - expenses, 0)
    debt_ratio = round((expenses / income) * 100, 2) if income else 0.0
    savings_rate = round((savings / income) * 100, 2) if income else 0.0

    # === AI Section (for summary & analysis) ===
    prompt = f"""
    You are a professional financial coach.
    Analyze the user's financial data:
    - Income: ₹{income}
    - Expenses: ₹{expenses}
    - Savings: ₹{savings}
    - Debt-to-Income Ratio: {debt_ratio}%
    - Savings Rate: {savings_rate}%
    - Transactions: {transactions}

    Write:
    ### Summary
    ### Strengths
    ### Areas to Improve
    ### Strategies
    ### Financial Fitness Score (1–10 with reason)
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert AI financial advisor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    raw = res.choices[0].message.content.strip()

    def extract(title):
        match = re.search(rf"### {title}\n([\s\S]*?)(?=\n###|\Z)", raw)
        return match.group(1).strip() if match else ""

    # === 🧩 Refined Spending Reallocation (Description-Based) ===
    reward_plan = []
    if isinstance(transactions_df, pd.DataFrame):
        try:
            desc_col = next((c for c in transactions_df.columns if "desc" in c.lower()), None)
            amt_col = next((c for c in transactions_df.columns if "amount" in c.lower()), None)
            cat_col = next((c for c in transactions_df.columns if "category" in c.lower()), None)

            if desc_col and amt_col:
                df = transactions_df.copy()
                df = df.dropna(subset=[desc_col, amt_col])
                df[desc_col] = df[desc_col].astype(str).str.strip().str.lower()

                # ✅ Filter only actual spending
                if cat_col:
                    df = df[~df[cat_col].str.lower().isin(["income", "investment", "savings"])]

                df = df[df[amt_col] < 0]  # Only negative amounts = expenses
                df["abs_amount"] = df[amt_col].abs()

                # === Group similar descriptions ===
                keywords_map = {
                    "Groceries": ["grocery", "mart", "store", "supermarket", "d-mart"],
                    "Rent": ["rent"],
                    "Utilities": ["electricity", "water", "internet", "bill", "recharge"],
                    "Food & Dining": ["restaurant", "food", "dining", "swiggy", "zomato", "cafe"],
                    "Shopping": ["shopping", "amazon", "flipkart", "mall"],
                    "Transport": ["fuel", "petrol", "uber", "ola", "bus", "taxi"],
                    "Entertainment": ["movie", "tickets", "netflix", "spotify", "ott"],
                    "Health & Fitness": ["gym", "membership", "health", "medicine"]
                }

                grouped = {cat: 0 for cat in keywords_map.keys()}

                for _, row in df.iterrows():
                    desc = row[desc_col]
                    amt = row["abs_amount"]
                    matched = False
                    for cat, kws in keywords_map.items():
                        if any(kw in desc for kw in kws):
                            grouped[cat] += amt
                            matched = True
                            break
                    if not matched:
                        grouped["Shopping"] += amt  # fallback bucket

                # Pick top spending categories
                top_expenses = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:5]

                for cat, total in top_expenses:
                    if total > 0:
                        cut = round(total * 0.15, 2)
                        potential = future_value(cut, 10, 3)
                        reward_plan.append({
                            "category": cat,
                            "cut": cut,
                            "potential": potential
                        })

                # Add summary insight from actual top descriptions
                top_desc = (
                    df.groupby(desc_col)["abs_amount"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(5)
                    .index.str.title()
                    .tolist()
                )
                reward_plan.append({
                    "category": "Top Spending Keywords",
                    "cut": 0,
                    "potential": 0,
                    "insight": f"Highest spends in: {', '.join(top_desc)}"
                })

        except Exception as e:
            print("⚠️ Error in description-based reallocation:", e)

    # === 🎯 Goal Planner ===
    goals_plan = {
        "Emergency Fund": {
            "target": round(income * 3, 2),
            "monthly_saving": round(income * 0.15, 2),
            "months_to_reach": round((income * 3) / (income * 0.15))
        },
        "Dream Car": {
            "target": 500000,
            "monthly_saving": round(income * 0.25, 2),
            "months_to_reach": round(500000 / (income * 0.25))
        },
    }

    # === 🧾 Return Final Report ===
    return {
        "Financial_Overview": {
            "Total Income (₹)": round(income, 2),
            "Total Expenses (₹)": round(expenses, 2),
            "Savings (₹)": round(savings, 2),
            "Debt-to-Income (%)": debt_ratio,
            "Savings Rate (%)": savings_rate,
        },
        "AI_Financial_Analysis": {
            "Summary": split_to_list(extract("Summary")),
            "Strengths": split_to_list(extract("Strengths")),
            "Areas_to_Improve": split_to_list(extract("Areas to Improve")),
            "Strategies": split_to_list(extract("Strategies")),
            "Financial_Fitness_Score": clean_text(extract("Financial Fitness Score")),
        },
        "Spending_Reallocation": reward_plan,
        "Goal_Based_Plan": goals_plan,
    }
    income = float(summary.get("total_income", 0))
    expenses = float(summary.get("total_expenses", 0))
    transactions = int(summary.get("transactions_count", 0))
    savings = max(income - expenses, 0)
    debt_ratio = round((expenses / income) * 100, 2) if income else 0.0
    savings_rate = round((savings / income) * 100, 2) if income else 0.0

    # === AI Summary ===
    prompt = f"""
    You are a certified AI financial advisor.
    The user's monthly summary:
    - Income: ₹{income}
    - Expenses: ₹{expenses}
    - Savings: ₹{savings}
    - Debt-to-Income Ratio: {debt_ratio}%
    - Savings Rate: {savings_rate}%
    - Transactions: {transactions}

    Provide:
    ### Summary
    ### Strengths
    ### Areas to Improve
    ### Strategies
    ### Financial Fitness Score (1–10 with reason)
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful, structured financial advisor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    raw = res.choices[0].message.content.strip()

    def extract(title):
        match = re.search(rf"### {title}\n([\s\S]*?)(?=\n###|\Z)", raw)
        return match.group(1).strip() if match else ""

    # 🧩 Dynamic Spending Reallocation based on 'Category' and 'Description'
    reward_plan = []
    if isinstance(transactions_df, pd.DataFrame):
        try:
            cat_col = next((c for c in transactions_df.columns if "category" in c.lower()), None)
            amt_col = next((c for c in transactions_df.columns if "amount" in c.lower()), None)
            desc_col = next((c for c in transactions_df.columns if "desc" in c.lower()), None)

            if amt_col and cat_col:
                df = transactions_df.copy()
                df = df.dropna(subset=[amt_col, cat_col])
                df = df[df[amt_col] < 0]  # Only expenses

                # Group by Category
                grouped = df.groupby(cat_col)[amt_col].sum().abs().sort_values(ascending=False).head(5)

                for category, total in grouped.items():
                    # Suggest cutting 10–15% of the largest expense categories
                    cut = round(total * 0.15, 2)
                    potential = future_value(cut, 10, 3)
                    reward_plan.append({
                        "category": category,
                        "cut": cut,
                        "potential": potential
                    })

                # If there's a Description column, include top keywords in reasoning
                if desc_col:
                    desc_keywords = ", ".join(
                        df[desc_col].astype(str).str.title().unique()[:5]
                    )
                    reward_plan.append({
                        "category": "Key Spend Insights",
                        "cut": 0,
                        "potential": 0,
                        "insight": f"Major spending detected in: {desc_keywords}"
                    })
        except Exception as e:
            print("⚠️ Dynamic spending reallocation error:", e)

    # 🏦 Goal-Based Planning
    goals_plan = {
        "Emergency Fund": {
            "target": round(income * 3, 2),
            "monthly_saving": round(income * 0.15, 2),
            "months_to_reach": round((income * 3) / (income * 0.15))
        },
        "Dream Car": {
            "target": 500000,
            "monthly_saving": round(income * 0.25, 2),
            "months_to_reach": round(500000 / (income * 0.25))
        }
    }

    # 🧾 Final structured response
    return {
        "Financial_Overview": {
            "Total Income (₹)": round(income, 2),
            "Total Expenses (₹)": round(expenses, 2),
            "Savings (₹)": round(savings, 2),
            "Debt-to-Income (%)": debt_ratio,
            "Savings Rate (%)": savings_rate,
        },
        "AI_Financial_Analysis": {
            "Summary": split_to_list(extract("Summary")),
            "Strengths": split_to_list(extract("Strengths")),
            "Areas_to_Improve": split_to_list(extract("Areas to Improve")),
            "Strategies": split_to_list(extract("Strategies")),
            "Financial_Fitness_Score": clean_text(extract("Financial Fitness Score")),
        },
        "Spending_Reallocation": reward_plan,
        "Goal_Based_Plan": goals_plan,
    }
    income = float(summary.get("total_income", 0))
    expenses = float(summary.get("total_expenses", 0))
    transactions = int(summary.get("transactions_count", 0))
    savings = max(income - expenses, 0)
    debt_ratio = round((expenses / income) * 100, 2) if income else 0.0
    savings_rate = round((savings / income) * 100, 2) if income else 0.0

    # 🧠 AI Prompt
    prompt = f"""
    You are a professional financial coach.
    Analyze the user's financial health:
    - Income: ₹{income}
    - Expenses: ₹{expenses}
    - Savings: ₹{savings}
    - Debt-to-Income Ratio: {debt_ratio}%
    - Savings Rate: {savings_rate}%
    - Transactions: {transactions}

    Include:
    ### Summary
    ### Strengths
    ### Areas to Improve
    ### Strategies
    ### Financial Fitness Score (1–10 with reason)
    """

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert AI financial advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    raw = res.choices[0].message.content.strip()

    def extract(title):
        match = re.search(rf"### {title}\n([\s\S]*?)(?=\n###|\Z)", raw)
        return match.group(1).strip() if match else ""

    # 🧩 Dynamic Spending Reallocation (based on actual transactions)
    reward_plan = []
    if isinstance(transactions_df, pd.DataFrame) and "amount" in transactions_df.columns:
        try:
            # Try to find a category/description column
            category_col = next(
                (col for col in transactions_df.columns if "category" in col.lower() or "description" in col.lower()),
                None
            )

            if category_col:
                # Aggregate negative (expense) transactions by category
                category_spending = (
                    transactions_df[transactions_df["amount"] < 0]
                    .groupby(category_col)["amount"]
                    .sum()
                    .abs()
                    .sort_values(ascending=False)
                    .head(4)
                )

                for cat, total in category_spending.items():
                    cut = round(total * 0.15, 2)  # suggest 15% reduction
                    potential = future_value(cut, 10, 3)
                    reward_plan.append({
                        "category": str(cat).title(),
                        "cut": cut,
                        "potential": potential
                    })

        except Exception as e:
            print("⚠️ Could not compute dynamic reward plan:", e)

    # fallback if no transactions or categories found
    if not reward_plan:
        reward_plan = [
            {"category": "Dining Out", "cut": 1500, "potential": future_value(1500, 10, 3)},
            {"category": "Streaming Services", "cut": 800, "potential": future_value(800, 10, 3)},
            {"category": "Online Shopping", "cut": 2000, "potential": future_value(2000, 10, 3)},
        ]

    # 🎯 Auto goal planner (based on income)
    goals_plan = {
        "Emergency Fund": {
            "target": round(income * 3, 2),
            "monthly_saving": round(income * 0.15, 2),
            "months_to_reach": round((income * 3) / (income * 0.15))
        },
        "Dream Car": {
            "target": 500000,
            "monthly_saving": round(income * 0.25, 2),
            "months_to_reach": round(500000 / (income * 0.25))
        }
    }

    return {
        "Financial_Overview": {
            "Total Income (₹)": round(income, 2),
            "Total Expenses (₹)": round(expenses, 2),
            "Savings (₹)": round(savings, 2),
            "Debt-to-Income (%)": debt_ratio,
            "Savings Rate (%)": savings_rate,
        },
        "AI_Financial_Analysis": {
            "Summary": split_to_list(extract("Summary")),
            "Strengths": split_to_list(extract("Strengths")),
            "Areas_to_Improve": split_to_list(extract("Areas to Improve")),
            "Strategies": split_to_list(extract("Strategies")),
            "Financial_Fitness_Score": clean_text(extract("Financial Fitness Score")),
        },
        "Spending_Reallocation": reward_plan,
        "Goal_Based_Plan": goals_plan,
    }