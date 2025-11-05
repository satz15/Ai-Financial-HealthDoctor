# 🩺 AI Financial Health Doctor

## 💡 Overview
**AI Financial Health Doctor** is an intelligent Python-based financial wellness assistant built using **FastAPI**.  
It acts like a *personal health tracker* — but for your finances.  
The app analyzes your **income, debt, expenses, savings, and credit score**, and gives a **Financial Fitness Score** with personalized recommendations.

---

## ⚙️ Setup Instructions

```bash
# Clone the repository
git clone https://github.com/satz15/Ai-Financial-HealthDoctor.git

# Move into the project directory
cd Ai-Financial-HealthDoctor

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# 🪟 Windows (Git Bash)
source venv/Scripts/activate

# 🐧 macOS / Linux
# source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Run the FastAPI application
uvicorn app.main:app --reload
