# 🎓 CampusFlow – Academic Management System

CampusFlow is a Flask web application for managing students, attendance, exam results and student feedback in one place. It includes PDF import for attendance and results, a dashboard with charts, printable report cards, and automatic Google Form generation for collecting student feedback.

## Features

- **Students** – add, edit, delete and list students (name, enrollment number, department, semester, section, email, status), with PDF import.
- **Attendance** – mark attendance manually or import it from a PDF (matched by enrollment number), with duplicate protection.
- **Results** – add, edit, view, delete and filter results by student, exam type and semester. Percentage and grade are calculated automatically. Results can also be imported from a PDF.
- **Report cards** – a per-student report card grouped by semester, with overall marks and a Print / Save as PDF button.
- **Dashboard** – count cards for students, attendance and results, plus charts for attendance (present vs absent, % by subject) and result trends (average % by exam and by subject).
- **Feedback** – generate one Google Form per student through the Google Forms API, copy or email the link, and track who has filled it (Pending / Filled, response rate).
- **Authentication** – user login with Flask-Login and Bcrypt.

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Frontend:** Jinja2 templates, Bootstrap 5, Bootstrap Icons, Chart.js
- **PDF import:** pdfplumber
- **Google integration:** Google Forms API (`google-api-python-client`, `google-auth-oauthlib`)

## Project Structure

```
Academic_Management_System/
├── run.py
├── config.py
├── requirements.txt
├── client_secret.json        # Google OAuth client (NOT committed)
├── instance/                 # local data + Google token (NOT committed)
└── app/
    ├── __init__.py           # app factory, blueprints, models
    ├── models/               # student, attendance, result, feedback, feedback_form, user
    ├── routes/               # auth, dashboard, students, attendance, results, feedback
    ├── services/             # google_forms.py (Google Forms API wrapper)
    ├── utils/                # PDF extractors (e.g. result_extractor.py)
    ├── templates/            # layout, dashboard, students, attendance, results, feedback
    └── static/               # css, js
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the app

Check `config.py` and set your secret key and database settings (use environment variables for anything private). Never commit real secrets.

### 5. Run the app

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser. Database tables are created automatically on first start.

## Importing from PDF

**Results** – Results → *Import PDF*. Enter the subject, exam type, semester and default max marks, then upload a PDF whose rows contain the student's enrollment number and marks (for example `45` or `45/50`). Students are matched by enrollment number; re-uploading the same subject, exam and semester skips duplicates.

**Attendance** – Attendance → *Upload PDF*. Enter the subject and date, then upload the PDF. Students are matched by enrollment number.

## Google Forms Feedback Setup

The feedback feature creates Google Forms through the Google Forms API, so it needs a one-time Google Cloud setup.

1. Create a project at the [Google Cloud Console](https://console.cloud.google.com/) and enable the **Google Forms API**.
2. Configure the **OAuth consent screen** (External) and add your Google account as a **test user**.
3. Create an **OAuth client ID** of type **Web application** with this authorized redirect URI:
   ```
   http://127.0.0.1:5000/feedback/google/callback
   ```
4. Download the JSON file and save it as `client_secret.json` in the project root (next to `run.py`).
5. Start the app, open **Feedback**, click **Connect Google**, and allow all requested permissions (including viewing form responses).
6. Click **Generate for all** to create one form per student. The page checks for new responses automatically; use **Check responses** to refresh on demand.

> Open the app at `127.0.0.1:5000` (not `localhost`) so the redirect URI matches. For a deployed site, add your live HTTPS URL plus `/feedback/google/callback` as another authorized redirect URI.
>
> `client_secret.json` and `instance/google_token.json` are secrets. They are listed in `.gitignore` and must never be pushed to GitHub.

## Roadmap

- AI assistant
- Role-based access (admin / teacher)
- Email delivery of feedback links directly from the app

## Author

Your Name – astha 

## License

Add a license of your choice (for example MIT) before sharing publicly.