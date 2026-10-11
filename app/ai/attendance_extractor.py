"""
attendance_extractor.py
-------------------------------------------------------
AI Attendance Information Extractor

Uses Gemini to extract structured attendance
(Enrollment No + Status) from uploaded PDFs.

Author: CampusFlow AI
"""

import json
import re

from app.ai.llm import get_llm


class AttendanceExtractor:

    def __init__(self):
        self.llm = get_llm()

    # =====================================================
    # Prompt
    # =====================================================

    def build_prompt(self, text):

        return f"""
You are an AI Attendance Information Extraction System.

Extract ALL attendance rows from the document.

Each row has a student's Enrollment Number and their
attendance Status (Present or Absent).

Return ONLY JSON.

Format:

[
  {{
    "enrollment_no":"",
    "status":""
  }}
]

Rules:

1. Return ONLY JSON.
2. No explanation.
3. No markdown.
4. No ```json.
5. Output must be a JSON array.
6. "status" must be exactly "Present" or "Absent"
   (normalize values like "P", "A", "present", "ABSENT",
   "1"/"0", "Yes"/"No" to one of these two values).
7. If status cannot be determined, use "".
8. If enrollment_no is missing, use "".
9. Preserve the original enrollment_no value exactly as
   written (do not reformat or guess).

Document:

{text}
"""

    # =====================================================
    # Convert Gemini Response to String
    # =====================================================

    def response_to_text(self, response):

        content = response.content

        # Gemini sometimes returns string
        if isinstance(content, str):
            return content

        # Gemini sometimes returns list
        if isinstance(content, list):

            text = ""

            for item in content:

                if hasattr(item, "text"):
                    text += item.text

                elif isinstance(item, dict):
                    text += item.get("text", "")

                else:
                    text += str(item)

            return text

        return str(content)

    # =====================================================
    # Clean Response
    # =====================================================

    def clean_response(self, response):

        response = self.response_to_text(response)

        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

        match = re.search(r"\[.*\]", response, re.DOTALL)

        if match:
            return match.group(0)

        return response

    # =====================================================
    # Extract Attendance Rows
    # =====================================================

    def extract_attendance(self, text):

        try:

            prompt = self.build_prompt(text)

            response = self.llm.invoke(prompt)

            cleaned = self.clean_response(response)

            print("\n========== GEMINI RESPONSE ==========")
            print(cleaned)
            print("=====================================\n")

            records = json.loads(cleaned)

            if isinstance(records, dict):
                records = [records]

            return self.get_valid_records(records)

        except Exception as e:

            print("\nGemini Extraction Error")
            print(e)

            return []

    # =====================================================
    # Safe String
    # =====================================================

    def safe_str(self, value):

        if value is None:
            return ""

        if isinstance(value, list):
            return " ".join(map(str, value))

        return str(value).strip()

    # =====================================================
    # Normalize Status
    # =====================================================

    def normalize_status(self, value):

        value = self.safe_str(value).lower()

        present_values = {
            "present", "p", "yes", "y", "1", "true"
        }

        absent_values = {
            "absent", "a", "no", "n", "0", "false"
        }

        if value in present_values:
            return "Present"

        if value in absent_values:
            return "Absent"

        return ""

    # =====================================================
    # Validate Record
    # =====================================================

    def validate_record(self, record):

        enrollment = self.safe_str(record.get("enrollment_no"))
        status = self.normalize_status(record.get("status"))

        if enrollment == "":
            return False

        if status == "":
            return False

        return True

    # =====================================================
    # Remove Duplicates
    # =====================================================

    def remove_duplicates(self, records):

        unique = []

        seen = set()

        for record in records:

            enrollment = self.safe_str(
                record.get("enrollment_no")
            )

            if enrollment in seen:
                continue

            seen.add(enrollment)

            unique.append(record)

        return unique

    # =====================================================
    # Return Valid Records
    # =====================================================

    def get_valid_records(self, records):

        valid = []

        for record in records:

            if self.validate_record(record):

                valid.append({
                    "enrollment_no": self.safe_str(
                        record.get("enrollment_no")
                    ),
                    "status": self.normalize_status(
                        record.get("status")
                    ),
                })

        return self.remove_duplicates(valid)
