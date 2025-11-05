from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PROJECT_NAME = "AI Financial Health Doctor"
    UPLOAD_FOLDER = "uploads"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()
