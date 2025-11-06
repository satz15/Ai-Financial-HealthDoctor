from fastapi import FastAPI, UploadFile, File
from fastapi.encoders import jsonable_encoder
from app.file_parser import parse_csv, parse_pdf
from app.analysis import analyze_financial_statement
from app.config import settings
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Financial Health Doctor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = settings.UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
def home():
    return {"message": "Welcome to AI Financial Health Doctor 👋 — Upload your bank statement (CSV or PDF)"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or PDF bank statement for AI analysis"""
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Parse uploaded file
    if file.filename.endswith(".csv"):
        summary = parse_csv(file_path)
    elif file.filename.endswith(".pdf"):
        summary = parse_pdf(file_path)
    else:
        return {"error": "Only CSV or PDF files supported"}

    # Analyze using AI
    result = analyze_financial_statement(summary)
    return jsonable_encoder({"Financial_Report": result})
