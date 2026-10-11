import os
from dotenv import load_dotenv

# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv()

# ==========================================================
# Base Directory
# ==========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    # ======================================================
    # Security
    # ======================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "CampusFlow@2026"
    )

    # ======================================================
    # Database
    # ======================================================

    INSTANCE_FOLDER = os.path.join(
        BASE_DIR,
        "instance"
    )

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(INSTANCE_FOLDER, 'campusflow.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ======================================================
    # Upload Folders
    # ======================================================

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "uploads"
    )

    # Students

    STUDENT_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "students"
    )

    STUDENT_PDF_FOLDER = os.path.join(
        STUDENT_FOLDER,
        "pdfs"
    )

    # Attendance

    ATTENDANCE_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "attendance"
    )

    ATTENDANCE_PDF_FOLDER = os.path.join(
        ATTENDANCE_FOLDER,
        "pdfs"
    )

    # Results

    RESULTS_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "results"
    )

    # Feedback

    FEEDBACK_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "feedback"
    )

    # Documents

    DOCUMENT_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "documents"
    )

    # ======================================================
    # AI / RAG Configuration
    # ======================================================

    VECTOR_DB_FOLDER = os.path.join(
        BASE_DIR,
        "vectorstore"
    )

    CHROMA_DB_FOLDER = os.path.join(
        BASE_DIR,
        "chroma_db"
    )

    GOOGLE_API_KEY = os.getenv(
        "GOOGLE_API_KEY"
    )

    LLM_MODEL = os.getenv(
        "LLM_MODEL",
        "gemini-2.5-flash"
    )

    # Updated Google Embedding Model
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "models/text-embedding-004"
    )

    # ======================================================
    # Upload Limits
    # ======================================================

    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            30 * 1024 * 1024
        )
    )

    # ======================================================
    # Allowed Extensions
    # ======================================================

    ALLOWED_PDF = {
        "pdf"
    }

    ALLOWED_EXCEL = {
        "xlsx",
        "xls",
        "csv"
    }

    ALLOWED_DOCUMENTS = {
        "pdf",
        "docx",
        "txt"
    }


# ==========================================================
# Create Required Directories Automatically
# ==========================================================

FOLDERS = [

    Config.INSTANCE_FOLDER,

    Config.UPLOAD_FOLDER,

    Config.STUDENT_FOLDER,

    Config.STUDENT_PDF_FOLDER,

    Config.ATTENDANCE_FOLDER,

    Config.ATTENDANCE_PDF_FOLDER,

    Config.RESULTS_FOLDER,

    Config.FEEDBACK_FOLDER,

    Config.DOCUMENT_FOLDER,

    Config.VECTOR_DB_FOLDER,

    Config.CHROMA_DB_FOLDER

]

for folder in FOLDERS:
    os.makedirs(folder, exist_ok=True)