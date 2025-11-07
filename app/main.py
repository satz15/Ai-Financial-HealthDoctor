# from fastapi import FastAPI, UploadFile, File
# from fastapi.encoders import jsonable_encoder
# from app.file_parser import parse_csv, parse_pdf
# from app.analysis import analyze_financial_statement
# from app.config import settings
# import os
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI(title="AI Financial Health Doctor")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# UPLOAD_FOLDER = settings.UPLOAD_FOLDER
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @app.get("/")
# def home():
#     return {"message": "Welcome to AI Financial Health Doctor 👋 — Upload your bank statement (CSV or PDF)"}

# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     """Upload a CSV or PDF bank statement for AI analysis"""
#     file_path = os.path.join(UPLOAD_FOLDER, file.filename)
#     with open(file_path, "wb") as f:
#         f.write(await file.read())

#     # Parse uploaded file
#     if file.filename.endswith(".csv"):
#         summary = parse_csv(file_path)
#     elif file.filename.endswith(".pdf"):
#         summary = parse_pdf(file_path)
#     else:
#         return {"error": "Only CSV or PDF files supported"}

#     # Analyze using AI
#     result = analyze_financial_statement(summary)
#     return jsonable_encoder({"Financial_Report": result})

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse , Response
from fastapi.encoders import jsonable_encoder
from app.file_parser import parse_csv, parse_pdf
from app.analysis import analyze_financial_statement
from fpdf import FPDF
import os, uuid, requests
from fastapi.middleware.cors import CORSMiddleware
import mimetypes

app = FastAPI(title="AI Financial Health Doctor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Define base directory (absolute path to app folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Use absolute paths instead of relative ones
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
FONT_FOLDER = os.path.join(BASE_DIR, "fonts")

# ✅ Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(FONT_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Welcome to AI Financial Health Doctor 👋 Upload your financial statement for insights."}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or PDF for AI-based financial analysis."""
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Detect and parse file type
    if file.filename.endswith(".csv"):
        summary = parse_csv(file_path)
    elif file.filename.endswith(".pdf"):
        summary = parse_pdf(file_path)
    else:
        return {"error": "Unsupported file format. Please upload CSV or PDF."}

    # Run AI analysis
    report = analyze_financial_statement(summary)

    # Generate and save report PDF
    pdf_filename = f"financial_report_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
    generate_pdf(report, pdf_path)

    # Return report and signal to show download button
    return jsonable_encoder({
        "Financial_Report": report,
        "Report_Available": True,  # ✅ Frontend uses this to show "Download Report"
        "Report_Name": pdf_filename
    })


# @app.get("/download-report/{filename}")
# async def download_report(filename: str):
#     """Download the generated financial report."""
#     file_path = os.path.join(REPORT_FOLDER, filename)

#     if os.path.exists(file_path):
#         return FileResponse(file_path, media_type="application/pdf", filename=filename)
#     return {"error": "Report not found."}

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
    # Remove emojis & high Unicode characters beyond BMP range
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
            # Using "-" bullet for maximum compatibility
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

    # Summary (list)
    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Summary", has_unicode), ln=1)
    add_list(sections.get("Summary", []))

    # Strengths (list)
    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Strengths", has_unicode), ln=1)
    add_list(sections.get("Strengths", []))

    # Areas to Improve (list)
    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Areas to Improve", has_unicode), ln=1)
    add_list(sections.get("Areas_to_Improve", []))

    # Strategies (list or paragraph)
    pdf.set_font(base_font, "B", 11)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt("Strategies", has_unicode), ln=1)
    strategies = sections.get("Strategies", [])
    if isinstance(strategies, list):
        add_list(strategies)
    else:
        add_paragraph(strategies)

    # Financial Fitness Score (paragraph)
    score = sections.get("Financial_Fitness_Score", "")
    if score:
        pdf.set_font(base_font, "B", 11)
        pdf.set_x(MARGIN_L)
        pdf.cell(0, 8, _safe_txt("Financial Fitness Score", has_unicode), ln=1)
        add_paragraph(score)

    # Footer
    from datetime import datetime
    pdf.set_y(-18)
    pdf.set_font(base_font, "I" if os.path.exists(italic_font) else "", 9)
    pdf.set_x(MARGIN_L)
    pdf.cell(0, 8, _safe_txt(f"Report generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", has_unicode), 0, 0, "C")

    # Save
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    pdf.output(pdf_path)

    """Generate a clean, well-aligned financial report PDF using NotoSans."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Font setup
    font_dir = FONT_FOLDER
    regular_font = os.path.join(font_dir, "NotoSans-Regular.ttf")
    bold_font = os.path.join(font_dir, "NotoSans-Bold.ttf")
    italic_font = os.path.join(font_dir, "NotoSans-Italic.ttf")

    has_unicode = os.path.exists(regular_font)

    if has_unicode:
        pdf.add_font("NotoSans", "", regular_font, uni=True)
        if os.path.exists(bold_font):
            pdf.add_font("NotoSans", "B", bold_font, uni=True)
        if os.path.exists(italic_font):
            pdf.add_font("NotoSans", "I", italic_font, uni=True)
        pdf.set_font("NotoSans", "", 14)
    else:
        pdf.set_font("Arial", "", 14)

    # Title
    pdf.cell(0, 10, txt="AI Financial Health Report", ln=True, align="C")
    pdf.ln(8)

    # Subtitle
    pdf.set_font("NotoSans" if has_unicode else "Arial", "I", 10)
    pdf.cell(0, 8, txt="Generated by AI Financial Doctor", ln=True, align="C")
    pdf.ln(10)

    # Financial Overview Section
    pdf.set_font("NotoSans" if has_unicode else "Arial", "B", 12)
    pdf.cell(0, 8, txt="Financial Overview", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("NotoSans" if has_unicode else "Arial", "", 11)
    for key, val in report["Financial_Overview"].items():
        pdf.cell(60, 8, txt=_safe_txt(f"{key}:", has_unicode), ln=0)
        pdf.cell(0, 8, txt=_safe_txt(str(val), has_unicode), ln=1)
    pdf.ln(8)

    # AI Financial Analysis Section
    pdf.set_font("NotoSans" if has_unicode else "Arial", "B", 12)
    pdf.cell(0, 8, txt="AI Financial Analysis", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    for section, content in report["AI_Financial_Analysis"].items():
        pdf.set_font("NotoSans" if has_unicode else "Arial", "B", 11)
        pdf.cell(0, 8, txt=_safe_txt(section.replace("_", " "), has_unicode), ln=True)
        pdf.ln(2)
        pdf.set_font("NotoSans" if has_unicode else "Arial", "", 10)

        if isinstance(content, list):
            for point in content:
                pdf.multi_cell(0, 7, _safe_txt(f"• {point}", has_unicode), align="L")
                pdf.ln(1)
        else:
            pdf.multi_cell(0, 7, _safe_txt(str(content), has_unicode), align="L")
        pdf.ln(4)

    # Footer
    from datetime import datetime
    pdf.set_y(-20)
    pdf.set_font("NotoSans" if has_unicode else "Arial", "I", 9)
    footer_text = f"Report generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    pdf.cell(0, 10, txt=_safe_txt(footer_text, has_unicode), align="C")

    # Save
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    pdf.output(name=pdf_path)




