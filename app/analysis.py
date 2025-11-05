from app.models import FinancialData

def analyze_financial_health(data: FinancialData):
    # Basic calculations
    debt_to_income = round((data.debts / data.income) * 100, 2)
    savings_rate = round((data.savings / data.income) * 100, 2)
    total_expenses = sum(e.amount for e in data.expenses)
    expense_to_income = round((total_expenses / data.income) * 100, 2)

    # Basic scoring
    score = 100
    if debt_to_income > 40: score -= 15
    if savings_rate < 20: score -= 10
    if expense_to_income > 70: score -= 10
    if data.credit_score < 650: score -= 15

    # Basic advice
    recommendations = []
    if debt_to_income > 40:
        recommendations.append("Reduce your debt-to-income ratio below 35%.")
    if savings_rate < 20:
        recommendations.append("Increase monthly savings by at least 5%.")
    if expense_to_income > 70:
        recommendations.append("Cut unnecessary expenses.")
    if data.credit_score < 650:
        recommendations.append("Improve your credit score by timely payments.")

    return {
        "Debt-to-Income (%)": debt_to_income,
        "Savings Rate (%)": savings_rate,
        "Expense-to-Income (%)": expense_to_income,
        "Credit Score": data.credit_score,
        "Financial Fitness Score": max(min(score, 100), 0),
        "Recommendations": recommendations or ["Your financial health looks good!"]
    }
