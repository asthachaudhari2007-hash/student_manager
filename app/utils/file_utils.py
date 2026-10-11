import os

# ==========================================================
# Allowed File Extensions
# ==========================================================

ALLOWED_PDF = {"pdf"}

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
# Get File Extension
# ==========================================================

def get_extension(filename):

    if "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


# ==========================================================
# Check PDF
# ==========================================================

def allowed_pdf(filename):

    return get_extension(filename) in ALLOWED_PDF


# ==========================================================
# Check Excel
# ==========================================================

def allowed_excel(filename):

    return get_extension(filename) in ALLOWED_EXCEL


# ==========================================================
# Check Documents
# ==========================================================

def allowed_document(filename):

    return get_extension(filename) in ALLOWED_DOCUMENTS


# ==========================================================
# Check File Exists
# ==========================================================

def file_exists(path):

    return os.path.isfile(path)


# ==========================================================
# Create Folder
# ==========================================================

def create_folder(path):

    os.makedirs(path, exist_ok=True)