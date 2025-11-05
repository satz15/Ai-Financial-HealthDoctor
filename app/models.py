from pydantic import BaseModel
from typing import List, Optional

class Expense(BaseModel):
    category: str
    amount: float

class FinancialData(BaseModel):
    income: float
    debts: float
    savings: float
    expenses: List[Expense]
    credit_score: Optional[int] = 700
