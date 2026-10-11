"""
Thin wrapper around the Google Forms API.

pip install google-api-python-client google-auth google-auth-oauthlib

Files used (both stay out of git!):
    <project>/client_secret.json        OAuth client downloaded from Google Cloud
    <project>/instance/google_token.json  created after the teacher clicks "Connect Google"
"""
import os
import re
from datetime import datetime

from flask import current_app
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]
# The bundled discovery file in the python client can be older than
# forms.setPublishSettings, so load the live one (same as Google's own sample).
DISCOVERY_URL = "https://forms.googleapis.com/$discovery/rest?version=v1"


class GoogleNotConnected(Exception):
    pass


# ----------------------------------------------------------------------
# Default questions in every student's form (edit freely)
# ----------------------------------------------------------------------
DEFAULT_DESCRIPTION = "Please share your honest feedback. It only takes a minute."

DEFAULT_QUESTIONS = [
    {"title": "How would you rate the teaching quality?", "type": "scale", "low": "Poor", "high": "Excellent"},
    {"title": "How would you rate the course content?", "type": "scale", "low": "Poor", "high": "Excellent"},
    {"title": "How would you rate the pace of the classes?", "type": "scale", "low": "Too slow/fast", "high": "Just right"},
    {"title": "Would you recommend this course to others?", "type": "choice", "options": ["Yes", "Maybe", "No"]},
    {"title": "What could be improved?", "type": "text", "required": False},
]


# ----------------------------------------------------------------------
# Paths + credentials
# ----------------------------------------------------------------------
def client_secret_path():
    return os.path.join(os.path.dirname(current_app.root_path), "client_secret.json")


def token_path():
    os.makedirs(current_app.instance_path, exist_ok=True)
    return os.path.join(current_app.instance_path, "google_token.json")


def has_client_secret():
    return os.path.exists(client_secret_path())


def save_credentials(creds):
    with open(token_path(), "w") as f:
        f.write(creds.to_json())


def load_credentials():
    path = token_path()
    if not os.path.exists(path):
        return None
    creds = Credentials.from_authorized_user_file(path, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(creds)
            except RefreshError:
                os.remove(path)          # token revoked/expired -> connect again
                return None
        else:
            return None
    return creds


def is_connected():
    return load_credentials() is not None


def disconnect():
    if os.path.exists(token_path()):
        os.remove(token_path())


def make_flow(redirect_uri):
    return Flow.from_client_secrets_file(
        client_secret_path(), scopes=SCOPES, redirect_uri=redirect_uri
    )


def get_service():
    creds = load_credentials()
    if creds is None:
        raise GoogleNotConnected("Google account is not connected.")
    return build("forms", "v1", credentials=creds,
                 discoveryServiceUrl=DISCOVERY_URL, static_discovery=False)


# ----------------------------------------------------------------------
# Building a form
# ----------------------------------------------------------------------
def build_requests(description, questions):
    """Turn our simple question dicts into Forms API batchUpdate requests."""
    requests = [{
        "updateFormInfo": {
            "info": {"description": description},
            "updateMask": "description",
        }
    }]

    for index, q in enumerate(questions):
        if q["type"] == "scale":
            question = {"scaleQuestion": {
                "low": 1, "high": 5,
                "lowLabel": q.get("low", ""), "highLabel": q.get("high", ""),
            }}
        elif q["type"] == "choice":
            question = {"choiceQuestion": {
                "type": "RADIO",
                "options": [{"value": o} for o in q["options"]],
            }}
        else:  # text
            question = {"textQuestion": {"paragraph": True}}

        question["required"] = q.get("required", True)
        requests.append({
            "createItem": {
                "item": {"title": q["title"], "questionItem": {"question": question}},
                "location": {"index": index},
            }
        })
    return requests


def create_feedback_form(service, title, description=DEFAULT_DESCRIPTION, questions=None):
    """Create + fill + publish one form. Returns ids/links."""
    questions = questions or DEFAULT_QUESTIONS

    # 1) create (the API only accepts a title at this step)
    form = service.forms().create(
        body={"info": {"title": title, "documentTitle": title}}
    ).execute()
    form_id = form["formId"]

    # 2) add description + questions
    service.forms().batchUpdate(
        formId=form_id,
        body={"requests": build_requests(description, questions)},
    ).execute()

    # 3) publish so it accepts responses (forms made by the API are
    #    unpublished by default now)
    service.forms().setPublishSettings(
        formId=form_id,
        body={"publishSettings": {"publishState": {
            "isPublished": True, "isAcceptingResponses": True}}},
    ).execute()

    responder_uri = form.get("responderUri")
    if not responder_uri:
        responder_uri = service.forms().get(formId=form_id).execute().get("responderUri")

    return {
        "form_id": form_id,
        "responder_url": responder_uri,
        "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
    }


# ----------------------------------------------------------------------
# Reading responses
# ----------------------------------------------------------------------
def _parse_time(value):
    """'2026-10-11T08:15:30.123456789Z' -> naive UTC datetime"""
    if not value:
        return None
    value = re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError:
        return None


def get_response_summary(service, form_id):
    """Returns (number_of_responses, time_of_latest_response)."""
    count, latest, token = 0, None, None
    while True:
        kwargs = {"formId": form_id}
        if token:
            kwargs["pageToken"] = token
        data = service.forms().responses().list(**kwargs).execute()
        for r in data.get("responses", []):
            count += 1
            t = _parse_time(r.get("lastSubmittedTime"))
            if t and (latest is None or t > latest):
                latest = t
        token = data.get("nextPageToken")
        if not token:
            return count, latest
