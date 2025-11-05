from fastapi import FastAPI
from app.models import FinancialData
from app.analysis import analyze_financial_health

app = FastAPI(title="AI Financial Health Doctor")

@app.get("/")
def home():
    return {"message": "Welcome to AI Financial Health Doctor 👋"}

@app.post("/analyze")
def analyze(data: FinancialData):
    result = analyze_financial_health(data)
    return {"Financial_Report": result}
