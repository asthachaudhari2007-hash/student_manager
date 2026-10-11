"""
student_extractor.py
-------------------------------------------------------
AI Student Information Extractor

Uses Gemini to extract structured student
information from uploaded PDFs.

Author: CampusFlow AI
"""

import json
import re

from app.ai.llm import get_llm


class StudentExtractor:

    def __init__(self):
        self.llm = get_llm()

    # =====================================================
    # Prompt
    # =====================================================

    def build_prompt(self, text):

        return f"""
You are an AI Student Information Extraction System.

Extract ALL students from the document.

Return ONLY JSON.

Format:

[
  {{
    "enrollment_no":"",
    "roll_no":"",
    "first_name":"",
    "last_name":"",
    "email":"",
    "phone":"",
    "gender":"",
    "department":"",
    "semester":"",
    "section":"",
    "admission_year":""
  }}
]

Rules:

1. Return ONLY JSON.
2. No explanation.
3. No markdown.
4. No ```json.
5. Output must be a JSON array.
6. If any field is missing use "".
7. Preserve original values.

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
    # Extract Students
    # =====================================================

    def extract_students(self, text):

        try:

            prompt = self.build_prompt(text)

            response = self.llm.invoke(prompt)

            cleaned = self.clean_response(response)

            print("\n========== GEMINI RESPONSE ==========")
            print(cleaned)
            print("=====================================\n")

            students = json.loads(cleaned)

            if isinstance(students, dict):
                students = [students]

            return self.get_valid_students(students)

        except Exception as e:

            print("\nGemini Extraction Error")
            print(e)

            return []

    # =====================================================
    # Safe Integer
    # =====================================================

    def safe_int(self, value):

        try:
            return int(str(value).strip())

        except Exception:
            return 0

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
    # Validate Student
    # =====================================================

    def validate_student(self, student):

        enrollment = self.safe_str(student.get("enrollment_no"))
        first_name = self.safe_str(student.get("first_name"))
        department = self.safe_str(student.get("department"))

        semester = self.safe_int(student.get("semester"))
        admission_year = self.safe_int(student.get("admission_year"))

        if enrollment == "":
            return False

        if first_name == "":
            return False

        if department == "":
            return False

        if semester <= 0:
            return False

        if admission_year <= 0:
            return False

        return True

    # =====================================================
    # Remove Duplicates
    # =====================================================

    def remove_duplicates(self, students):

        unique = []

        seen = set()

        for student in students:

            enrollment = self.safe_str(
                student.get("enrollment_no")
            )

            if enrollment in seen:
                continue

            seen.add(enrollment)

            unique.append(student)

        return unique

    # =====================================================
    # Return Valid Students
    # =====================================================

    def get_valid_students(self, students):

        valid = []

        for student in students:

            if self.validate_student(student):
                valid.append(student)

        return self.remove_duplicates(valid)