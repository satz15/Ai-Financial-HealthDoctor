import pandas as pd
import pdfplumber

def parse_csv(file_path: str):
    df = pd.read_csv(file_path)
    amount_col = [col for col in df.columns if "amount" in col.lower()]
    if not amount_col:
        raise ValueError("No 'Amount' column found in CSV")

    total_income = df[df[amount_col[0]] > 0][amount_col[0]].sum()
    total_expenses = abs(df[df[amount_col[0]] < 0][amount_col[0]].sum())

    return {
        "total_income": round(float(total_income), 2),
        "total_expenses": round(float(total_expenses), 2),
        "transactions_count": int(len(df))
    }

def parse_pdf(file_path: str):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return {"raw_text": text[:1000]}
