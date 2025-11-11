# from fastapi import FastAPI, UploadFile, File
# from fastapi.responses import FileResponse , Response
# from fastapi.encoders import jsonable_encoder
# import pandas as pd
# from app.file_parser import parse_csv, parse_pdf
# from app.analysis import analyze_financial_statement
# from fpdf import FPDF
# import os, uuid, requests
# from fastapi.middleware.cors import CORSMiddleware
# import json
# from datetime import datetime
# from pydantic import BaseModel
# from groq import Groq
# from dotenv import load_dotenv

# load_dotenv()
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# app = FastAPI(title="AI Financial Health Doctor")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class Query(BaseModel):
#     question: str


# # ✅ Define base directory (absolute path to app folder)
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # ✅ Use absolute paths instead of relative ones
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
# REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
# FONT_FOLDER = os.path.join(BASE_DIR, "fonts")
# HISTORY_FILE = os.path.join(BASE_DIR, "reports", "financial_history.json")

# # ✅ Ensure folders exist
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(REPORT_FOLDER, exist_ok=True)
# os.makedirs(FONT_FOLDER, exist_ok=True)


# @app.get("/")
# def home():
#     return {"message": "Welcome to AI Financial Health Doctor 👋 Upload your financial statement for insights."}


# def save_monthly_summary(report, transactions_df=None):
#     """
#     Save monthly summary (income, expenses, savings).
#     If transactions_df has a date/month column, derive month from it;
#     otherwise, fallback to current system month.
#     """
#     from dateutil import parser

#     def extract_month_from_df(df):
#         """Try to detect month from any date-like column."""
#         if df is None or df.empty:
#             return None

#         # Common column name candidates
#         possible_cols = [c for c in df.columns if any(x in c.lower() for x in ["date", "month", "time"])]
#         if not possible_cols:
#             return None

#         for col in possible_cols:
#             try:
#                 # Try parsing the first valid date
#                 valid_dates = pd.to_datetime(df[col], errors="coerce")
#                 valid = valid_dates.dropna()
#                 if not valid.empty:
#                     # Example: 2025-10 for October 2025
#                     return valid.iloc[0].strftime("%Y-%m")
#             except Exception:
#                 continue
#         return None

#     # 🕐 Detect month automatically
#     month_str = extract_month_from_df(transactions_df)
#     if not month_str:
#         month_str = datetime.now().strftime("%Y-%m")

#     history = []
#     if os.path.exists(HISTORY_FILE):
#         with open(HISTORY_FILE, "r") as f:
#             try:
#                 history = json.load(f)
#             except json.JSONDecodeError:
#                 history = []

#     # 🧾 Prepare new entry
#     summary = {
#         "month": month_str,
#         "income": report["Financial_Overview"]["Total Income (₹)"],
#         "expenses": report["Financial_Overview"]["Total Expenses (₹)"],
#         "savings": report["Financial_Overview"]["Savings (₹)"]
#     }

#     # Remove any old data for same month
#     history = [h for h in history if h["month"] != month_str]
#     history.append(summary)

#     # Sort by month chronologically
#     history.sort(key=lambda x: x["month"])

#     # Save to file
#     os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
#     with open(HISTORY_FILE, "w") as f:
#         json.dump(history, f, indent=4)
      


# @app.get("/financial-history")
# def get_financial_history():
#     if not os.path.exists(HISTORY_FILE):
#         return {"history": []}
#     with open(HISTORY_FILE, "r") as f:
#         history = json.load(f)
#     return {"history": history}

# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     """Upload a CSV or PDF for AI-based financial analysis."""
#     file_path = os.path.join(UPLOAD_FOLDER, file.filename)
#     with open(file_path, "wb") as f:
#         f.write(await file.read())

#     transactions_df = None  # we'll use this for dynamic spending logic

#     # Detect and parse file type
#     if file.filename.endswith(".csv"):
#         # parse summary
#         summary = parse_csv(file_path)
#         # also load the full CSV for category-level analysis
#         transactions_df = pd.read_csv(file_path)
#     elif file.filename.endswith(".pdf"):
#         summary = parse_pdf(file_path)
#     else:
#         return {"error": "Unsupported file format. Please upload CSV or PDF."}

#     # 🧠 Run AI + dynamic financial analysis
#     report = analyze_financial_statement(summary, transactions_df=transactions_df)

#     save_monthly_summary(report, transactions_df)

#     # Generate and save report PDF
#     pdf_filename = f"financial_report_{uuid.uuid4().hex[:6]}.pdf"
#     pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
#     generate_pdf(report, pdf_path)

#     # Return the full structured financial report
#     return jsonable_encoder({
#         "Financial_Report": report,
#         "Report_Available": True,
#         "Report_Name": pdf_filename
#     })

# @app.get("/download-report/{filename}")
# async def download_report(filename: str):
#     """Download the generated financial report."""
#     file_path = os.path.join(REPORT_FOLDER, filename)

#     if not os.path.exists(file_path):
#         return Response(
#             content=f"Report not found at: {file_path}",
#             status_code=404,
#             media_type="text/plain"
#         )

#     return FileResponse(
#         path=file_path,
#         media_type="application/pdf",
#         filename=filename,
#         headers={"Content-Disposition": f"attachment; filename={filename}"}
#     )

# def _safe_txt(s: str, can_unicode: bool) -> str:
#     """Sanitize text for FPDF: remove emojis and replace ₹ if needed."""
#     # Remove emojis & high Unicode characters beyond BMP range
#     s = ''.join(ch for ch in s if ord(ch) < 10000)
#     return s if can_unicode else s.replace("₹", "INR ")

# def generate_pdf(report, pdf_path):
#     """Generate a clean, well-aligned financial report PDF using NotoSans."""
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)

#     # Page + margins
#     MARGIN_L, MARGIN_R, MARGIN_T = 15, 15, 15
#     pdf.set_left_margin(MARGIN_L)
#     pdf.set_right_margin(MARGIN_R)
#     pdf.set_top_margin(MARGIN_T)
#     pdf.add_page()

#     content_w = pdf.w - MARGIN_L - MARGIN_R  # usable width

#     # Fonts
#     font_dir = FONT_FOLDER
#     regular_font = os.path.join(font_dir, "NotoSans-Regular.ttf")
#     bold_font    = os.path.join(font_dir, "NotoSans-Bold.ttf")
#     italic_font  = os.path.join(font_dir, "NotoSans-Italic.ttf")
#     has_unicode  = os.path.exists(regular_font)

#     if has_unicode:
#         pdf.add_font("NotoSans", "", regular_font, uni=True)
#         if os.path.exists(bold_font):   pdf.add_font("NotoSans", "B", bold_font, uni=True)
#         if os.path.exists(italic_font): pdf.add_font("NotoSans", "I", italic_font, uni=True)
#         base_font = "NotoSans"
#     else:
#         base_font = "Arial"

#     # Helpers
#     def hline():
#         y = pdf.get_y()
#         pdf.set_draw_color(210, 210, 210)
#         pdf.line(MARGIN_L, y, pdf.w - MARGIN_R, y)

#     def add_kv(label, value, label_w=70):
#         pdf.set_font(base_font, "", 11)
#         pdf.set_x(MARGIN_L)
#         pdf.cell(label_w, 7, _safe_txt(f"{label}:", has_unicode), ln=0)
#         pdf.cell(0, 7, _safe_txt(str(value), has_unicode), ln=1)

#     def add_heading(text, size=12, bold=True, gap=6):
#         pdf.set_x(MARGIN_L)
#         pdf.set_font(base_font, "B" if bold else "", size)
#         pdf.cell(0, 8, _safe_txt(text, has_unicode), ln=1)
#         hline()
#         pdf.ln(gap)

#     def add_list(items, indent=6, lh=7):
#         if not items:
#             return
#         pdf.set_font(base_font, "", 10)
#         for it in items:
#             pdf.set_x(MARGIN_L + indent)
#             # Using "-" bullet for maximum compatibility
#             pdf.multi_cell(content_w - indent, lh, _safe_txt(f"- {it}", has_unicode), align="L")
#             pdf.ln(1)

#     def add_paragraph(text, lh=7):
#         if not text:
#             return
#         pdf.set_x(MARGIN_L)
#         pdf.set_font(base_font, "", 10)
#         pdf.multi_cell(content_w, lh, _safe_txt(str(text), has_unicode), align="L")
#         pdf.ln(3)

#     # Title
#     pdf.set_font(base_font, "", 15)
#     pdf.set_x(MARGIN_L)
#     pdf.cell(0, 10, _safe_txt("AI Financial Health Report", has_unicode), ln=1, align="C")
#     pdf.ln(4)

#     # Financial Overview
#     add_heading("Financial Overview")
#     for k, v in report["Financial_Overview"].items():
#         add_kv(k, v)
#     pdf.ln(6)

#     # AI Sections
#     add_heading("AI Financial Analysis")
#     sections = report.get("AI_Financial_Analysis", {})

#     # Summary (list)
#     pdf.set_font(base_font, "B", 11)
#     pdf.set_x(MARGIN_L)
#     pdf.cell(0, 8, _safe_txt("Summary", has_unicode), ln=1)
#     add_list(sections.get("Summary", []))

#     # Strengths (list)
#     pdf.set_font(base_font, "B", 11)
#     pdf.set_x(MARGIN_L)
#     pdf.cell(0, 8, _safe_txt("Strengths", has_unicode), ln=1)
#     add_list(sections.get("Strengths", []))

#     # Areas to Improve (list)
#     pdf.set_font(base_font, "B", 11)
#     pdf.set_x(MARGIN_L)
#     pdf.cell(0, 8, _safe_txt("Areas to Improve", has_unicode), ln=1)
#     add_list(sections.get("Areas_to_Improve", []))

#     # Strategies (list or paragraph)
#     pdf.set_font(base_font, "B", 11)
#     pdf.set_x(MARGIN_L)
#     pdf.cell(0, 8, _safe_txt("Strategies", has_unicode), ln=1)
#     strategies = sections.get("Strategies", [])
#     if isinstance(strategies, list):
#         add_list(strategies)
#     else:
#         add_paragraph(strategies)

#     # Financial Fitness Score (paragraph)
#     score = sections.get("Financial_Fitness_Score", "")
#     if score:
#         pdf.set_font(base_font, "B", 11)
#         pdf.set_x(MARGIN_L)
#         pdf.cell(0, 8, _safe_txt("Financial Fitness Score", has_unicode), ln=1)
#         add_paragraph(score)

#     # Footer
#     from datetime import datetime
#     pdf.set_y(-18)
#     pdf.set_font(base_font, "I" if os.path.exists(italic_font) else "", 9)
#     pdf.set_x(MARGIN_L)
#     pdf.cell(0, 8, _safe_txt(f"Report generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", has_unicode), 0, 0, "C")

#     # Save
#     os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
#     pdf.output(pdf_path)

#     """Generate a clean, well-aligned financial report PDF using NotoSans."""
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()

#     # Font setup
#     font_dir = FONT_FOLDER
#     regular_font = os.path.join(font_dir, "NotoSans-Regular.ttf")
#     bold_font = os.path.join(font_dir, "NotoSans-Bold.ttf")
#     italic_font = os.path.join(font_dir, "NotoSans-Italic.ttf")

#     has_unicode = os.path.exists(regular_font)

#     if has_unicode:
#         pdf.add_font("NotoSans", "", regular_font, uni=True)
#         if os.path.exists(bold_font):
#             pdf.add_font("NotoSans", "B", bold_font, uni=True)
#         if os.path.exists(italic_font):
#             pdf.add_font("NotoSans", "I", italic_font, uni=True)
#         pdf.set_font("NotoSans", "", 14)
#     else:
#         pdf.set_font("Arial", "", 14)

#     # Title
#     pdf.cell(0, 10, txt="AI Financial Health Report", ln=True, align="C")
#     pdf.ln(8)

#     # Subtitle
#     pdf.set_font("NotoSans" if has_unicode else "Arial", "I", 10)
#     pdf.cell(0, 8, txt="Generated by AI Financial Doctor", ln=True, align="C")
#     pdf.ln(10)

#     # Financial Overview Section
#     pdf.set_font("NotoSans" if has_unicode else "Arial", "B", 12)
#     pdf.cell(0, 8, txt="Financial Overview", ln=True)
#     pdf.set_draw_color(200, 200, 200)
#     pdf.line(10, pdf.get_y(), 200, pdf.get_y())
#     pdf.ln(6)

#     pdf.set_font("NotoSans" if has_unicode else "Arial", "", 11)
#     for key, val in report["Financial_Overview"].items():
#         pdf.cell(60, 8, txt=_safe_txt(f"{key}:", has_unicode), ln=0)
#         pdf.cell(0, 8, txt=_safe_txt(str(val), has_unicode), ln=1)
#     pdf.ln(8)

#     # AI Financial Analysis Section
#     pdf.set_font("NotoSans" if has_unicode else "Arial", "B", 12)
#     pdf.cell(0, 8, txt="AI Financial Analysis", ln=True)
#     pdf.line(10, pdf.get_y(), 200, pdf.get_y())
#     pdf.ln(6)

#     for section, content in report["AI_Financial_Analysis"].items():
#         pdf.set_font("NotoSans" if has_unicode else "Arial", "B", 11)
#         pdf.cell(0, 8, txt=_safe_txt(section.replace("_", " "), has_unicode), ln=True)
#         pdf.ln(2)
#         pdf.set_font("NotoSans" if has_unicode else "Arial", "", 10)

#         if isinstance(content, list):
#             for point in content:
#                 pdf.multi_cell(0, 7, _safe_txt(f"• {point}", has_unicode), align="L")
#                 pdf.ln(1)
#         else:
#             pdf.multi_cell(0, 7, _safe_txt(str(content), has_unicode), align="L")
#         pdf.ln(4)

#     # Footer
#     from datetime import datetime
#     pdf.set_y(-20)
#     pdf.set_font("NotoSans" if has_unicode else "Arial", "I", 9)
#     footer_text = f"Report generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
#     pdf.cell(0, 10, txt=_safe_txt(footer_text, has_unicode), align="C")

#     # Save
#     os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
#     pdf.output(name=pdf_path)

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os, uuid, json
from datetime import datetime
import pandas as pd
from fpdf import FPDF

# App modules
from app.file_parser import parse_csv, parse_pdf
from app.analysis import analyze_financial_statement

# AI client
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI(title="AI Financial Health Doctor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
FONT_FOLDER = os.path.join(BASE_DIR, "fonts")
HISTORY_FILE = os.path.join(REPORT_FOLDER, "financial_history.json")
LAST_REPORT_FILE = os.path.join(REPORT_FOLDER, "last_report.json")

# Ensure folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(FONT_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Welcome to AI Financial Health Doctor 👋 Upload your financial statement for insights."}


def save_monthly_summary(report, transactions_df=None):
    """
    Save monthly summary (income, expenses, savings).
    If transactions_df has a date/month column, derive month from it;
    otherwise, fallback to current system month.
    """
    def extract_month_from_df(df: pd.DataFrame | None):
        if df is None or df.empty:
            return None
        # Try common date-like columns
        candidates = [c for c in df.columns if any(x in c.lower() for x in ["date", "month", "time"])]
        if not candidates:
            return None
        for col in candidates:
            try:
                ser = pd.to_datetime(df[col], errors="coerce")
                ser = ser.dropna()
                if not ser.empty:
                    return ser.iloc[0].strftime("%Y-%m")
            except Exception:
                continue
        return None

    month_str = extract_month_from_df(transactions_df) or datetime.now().strftime("%Y-%m")

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    summary = {
        "month": month_str,
        "income": report["Financial_Overview"]["Total Income (₹)"],
        "expenses": report["Financial_Overview"]["Total Expenses (₹)"],
        "savings": report["Financial_Overview"]["Savings (₹)"],
    }

    # upsert by month
    history = [h for h in history if h.get("month") != month_str]
    history.append(summary)
    history.sort(key=lambda x: x["month"])

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


@app.get("/financial-history")
def get_financial_history():
    if not os.path.exists(HISTORY_FILE):
        return {"history": []}
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
    return {"history": history}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or PDF for AI-based financial analysis."""
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    transactions_df = None

    # Detect and parse file type
    if file.filename.lower().endswith(".csv"):
        summary = parse_csv(file_path)
        transactions_df = pd.read_csv(file_path)
    elif file.filename.lower().endswith(".pdf"):
        summary = parse_pdf(file_path)
    else:
        return {"error": "Unsupported file format. Please upload CSV or PDF."}

    # AI + dynamic analysis
    report = analyze_financial_statement(summary, transactions_df=transactions_df)

    # Save monthly summary for trendline
    save_monthly_summary(report, transactions_df)

    # Persist last full report as JSON for /ask-ai context
    with open(LAST_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Generate PDF
    pdf_filename = f"financial_report_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
    generate_pdf(report, pdf_path)

    return jsonable_encoder({
        "Financial_Report": report,
        "Report_Available": True,
        "Report_Name": pdf_filename
    })


@app.get("/download-report/{filename}")
async def download_report(filename: str):
    """Download the generated financial report."""
    file_path = os.path.join(REPORT_FOLDER, filename)
    if not os.path.exists(file_path):
        return Response(
            content=f"Report not found at: {file_path}",
            status_code=404,
            media_type="text/plain"
        )
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _safe_txt(s: str, can_unicode: bool) -> str:
    """Sanitize text for FPDF: remove emojis and replace ₹ if needed."""
    s = ''.join(ch for ch in s if ord(ch) < 10000)
    return s if can_unicode else s.replace("₹", "INR ")


def generate_pdf(report, pdf_path):
    """Generate a clean, well-aligned financial report PDF using NotoSans."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page + margins
    MARGIN_L, MARGIN_R, MARGIN_T = 15, 15, 15
    pdf.set_left_margin(MARGIN_L)
    pdf.set_right_margin(MARGIN_R)
    pdf.set_top_margin(MARGIN_T)
    pdf.add_page()

    content_w = pdf.w - MARGIN_L - MARGIN_R  # usable width

    # Fonts
    font_dir = FONT_FOLDER
    regular_font = os.path.join(font_dir, "NotoSans-Regular.ttf")
    bold_font    = os.path.join(font_dir, "NotoSans-Bold.ttf")
    italic_font  = os.path.join(font_dir, "NotoSans-Italic.ttf")
    has_unicode  = os.path.exists(regular_font)

    if has_unicode:
        pdf.add_font("NotoSans", "", regular_font, uni=True)
        if os.path.exists(bold_font):   pdf.add_font("NotoSans", "B", bold_font, uni=True)
        if os.path.exists(italic_font): pdf.add_font("NotoSans", "I", italic_font, uni=True)
        base_font = "NotoSans"
    else:
        base_font = "Arial"

    # Helpers
    def hline():
        y = pdf.get_y()
        pdf.set_draw_color(210, 210, 210)
        pdf.line(MARGIN_L, y, pdf.w - MARGIN_R, y)

    def add_kv(label, value, label_w=70):
        pdf.set_font(base_font, "", 11)
        pdf.set_x(MARGIN_L)
        pdf.cell(label_w, 7, _safe_txt(f"{label}:", has_unicode), ln=0)
        pdf.cell(0, 7, _safe_txt(str(value), has_unicode), ln=1)

    def add_heading(text, size=12, bold=True, gap=6):
        pdf.set_x(MARGIN_L)
        pdf.set_font(base_font, "B" if bold else "", size)
        pdf.cell(0, 8, _safe_txt(text, has_unicode), ln=1)
        hline()
        pdf.ln(gap)

    def add_list(items, indent=6, lh=7):
        if not items:
            return
        pdf.set_font(base_font, "", 10)
        for it in items:
            pdf.set_x(MARGIN_L + indent)
            pdf.multi_cell(content_w - indent, lh, _safe_txt(f"- {it}", has_unicode), align="L")
            pdf.ln(1)

    def add_paragraph(text, lh=7):
        if not text:
            return
        pdf.set_x(MARGIN_L)
        pdf.set_font(base_font, "", 10)
        pdf.multi_cell(content_w, lh, _safe_txt(str(text), has_unicode), align="L")
        pdf.ln(3)

    # Title
    pdf.set_font(base_font, "", 15)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 10, _safe_txt("AI Financial Health Report", has_unicode), ln=1, align="C")
    pdf.ln(4)

    # Financial Overview
    add_heading("Financial Overview")
    for k, v in report["Financial_Overview"].items():
        add_kv(k, v)
    pdf.ln(6)

    # AI Sections
    add_heading("AI Financial Analysis")
    sections = report.get("AI_Financial_Analysis", {})

    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Summary", has_unicode), ln=1)
    add_list(sections.get("Summary", []))

    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Strengths", has_unicode), ln=1)
    add_list(sections.get("Strengths", []))

    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Areas to Improve", has_unicode), ln=1)
    add_list(sections.get("Areas_to_Improve", []))

    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Strategies", has_unicode), ln=1)
    strategies = sections.get("Strategies", [])
    if isinstance(strategies, list):
        add_list(strategies)
    else:
        add_paragraph(strategies)

    score = sections.get("Financial_Fitness_Score", "")
    if score:
        pdf.set_font(base_font, "B", 11)
        pdf.set_x(MARGIN_L)
        pdf.cell(0, 8, _safe_txt("Financial Fitness Score", has_unicode), ln=1)
        add_paragraph(score)

    # Spending Reallocation (if present)
    reallocation = report.get("Spending_Reallocation")
    if isinstance(reallocation, list) and reallocation:
        add_heading("Spending Reallocation & Rewards Plan")
        pdf.set_font(base_font, "", 10)
        for item in reallocation:
            line = f"{item.get('category')}: Reduce ₹{item.get('cut')} → 3-year potential ₹{item.get('potential')}"
            if item.get("insight"):
                line = f"Insight — {item['insight']}"
            pdf.multi_cell(0, 7, _safe_txt(line, has_unicode), align="L")
            pdf.ln(1)

    # Goal-Based Plan (if present)
    goals = report.get("Goal_Based_Plan")
    if isinstance(goals, dict) and goals:
        add_heading("Goal-Based Financial Plan")
        pdf.set_font(base_font, "", 10)
        for gname, gval in goals.items():
            line = (
                f"{gname}: target ₹{gval.get('target')}, "
                f"save ₹{gval.get('monthly_saving')}/mo → months {gval.get('months_to_reach')}"
            )
            pdf.multi_cell(0, 7, _safe_txt(line, has_unicode), align="L")
            pdf.ln(1)

    # Footer
    pdf.set_y(-18)
    pdf.set_font(base_font, "I" if os.path.exists(os.path.join(FONT_FOLDER, "NotoSans-Italic.ttf")) else "", 9)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt(f"Report generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", has_unicode), 0, 0, "C")

    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    pdf.output(pdf_path)


@app.post("/ask-ai")
async def ask_ai(query: Query):
    """
    Chat-based AI coach using the last saved financial report context.
    Falls back to history if last report JSON is missing.
    """
    context = {}

    # Prefer last full report (JSON)
    if os.path.exists(LAST_REPORT_FILE):
        try:
            with open(LAST_REPORT_FILE, "r", encoding="utf-8") as f:
                context = json.load(f)
        except Exception:
            context = {}

    # Fallback to last month from history
    if not context and os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                h = json.load(f)
                if isinstance(h, list) and h:
                    last = sorted(h, key=lambda x: x["month"])[-1]
                    context = {
                        "Financial_Overview": {
                            "Total Income (₹)": last.get("income"),
                            "Total Expenses (₹)": last.get("expenses"),
                            "Savings (₹)": last.get("savings"),
                        }
                    }
        except Exception:
            pass

    # Build a compact context summary
    def mk_ctx(c: dict) -> str:
        if not isinstance(c, dict):
            return "No context."
        fo = c.get("Financial_Overview", {})
        aa = c.get("AI_Financial_Analysis", {})
        sr = c.get("Spending_Reallocation", [])
        gb = c.get("Goal_Based_Plan", {})
        lines = []
        if fo:
            lines.append(
                f"Overview → Income: ₹{fo.get('Total Income (₹)')}, "
                f"Expenses: ₹{fo.get('Total Expenses (₹)')}, "
                f"Savings: ₹{fo.get('Savings (₹)')}"
            )
        if isinstance(aa, dict):
            summ = aa.get("Summary", [])
            if isinstance(summ, list) and summ:
                lines.append("Summary: " + " ".join(summ[:2]))
        if isinstance(sr, list) and sr:
            cats = [i.get("category") for i in sr if i.get("category")]
            if cats:
                lines.append("Spending targets: " + ", ".join(cats[:5]))
        if isinstance(gb, dict) and gb:
            lines.append("Goals: " + ", ".join(list(gb.keys())[:4]))
        return "\n".join(lines) if lines else "No context."

    compact_context = mk_ctx(context)

    prompt = f"""
You are a professional personal finance AI coach.

Use the user's last financial report context to give precise, practical advice.

--- Context ---
{compact_context}

--- User Question ---
{query.question}

Now respond as exactly 5 clear, numbered bullet points like this format:

1 Short actionable suggestion (include ₹ values or % where possible)  
2️ Explanation of tradeoff or risk  
3️ Next step or habit to implement  
4️ Simple investment or saving recommendation  
5️ One motivational insight or mindset shift  

Rules:
- Keep each point to one concise line.  
- Never use long paragraphs or filler text.  
- If you mention investments, note basic risk level (Low/Med/High).  
"""


    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful and analytical financial coach."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    answer = res.choices[0].message.content.strip()
    return {"response": answer}
   




