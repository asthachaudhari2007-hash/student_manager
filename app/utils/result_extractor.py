"""
Extract (enrollment_no, marks, max_marks) rows from a results PDF.

Needs:  pip install pdfplumber

The extractor only picks rows whose enrollment number is in `known_enrollments`
(the students already in your database), so header/footer lines and page numbers
are ignored automatically.
"""
import re

import pdfplumber

NUM = re.compile(r"^\d+(?:\.\d+)?$")
FRACTION = re.compile(r"^(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)$")


class ResultExtractor:

    def __init__(self, known_enrollments):
        # normalise once: "21cse001" == "21CSE001"
        self.known = {str(e).strip().upper(): str(e).strip() for e in known_enrollments if e}

    # ------------------------------------------------------------------
    def extract(self, file_stream):
        """Returns a list of dicts: {"enrollment_no", "marks", "max_marks" (or None)}"""
        rows = []
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                found = self._from_tables(page)
                if not found:                      # no table lines in PDF -> read as text
                    found = self._from_text(page)
                rows.extend(found)
        return rows

    # ------------------------------------------------------------------
    def _match_enrollment(self, text):
        return self.known.get(str(text or "").strip().upper())

    def _numbers_after(self, cells):
        """cells after the enrollment cell -> (marks, max_marks)"""
        marks = max_marks = None
        for c in cells:
            c = str(c or "").strip()
            m = FRACTION.match(c)
            if m:
                return float(m.group(1)), float(m.group(2))
            if NUM.match(c):
                if marks is None:
                    marks = float(c)
                elif max_marks is None:
                    max_marks = float(c)
                    break
        return marks, max_marks

    # ------------------------------------------------------------------
    def _from_tables(self, page):
        out = []
        for table in page.extract_tables() or []:
            header = [str(c or "").strip().lower() for c in (table[0] if table else [])]
            marks_col = next((i for i, h in enumerate(header) if "mark" in h and "max" not in h and "total" not in h), None)
            max_col = next((i for i, h in enumerate(header) if "max" in h or "out of" in h or "total" in h), None)

            for row in table:
                row = [str(c or "").strip() for c in row]
                enr_idx = next((i for i, c in enumerate(row) if self._match_enrollment(c)), None)
                if enr_idx is None:
                    continue
                enrollment = self._match_enrollment(row[enr_idx])

                marks = max_marks = None
                if marks_col is not None and marks_col < len(row) and NUM.match(row[marks_col]):
                    marks = float(row[marks_col])
                    if max_col is not None and max_col < len(row) and NUM.match(row[max_col]):
                        max_marks = float(row[max_col])
                if marks is None:
                    marks, max_marks = self._numbers_after(row[enr_idx + 1:])
                if marks is None:
                    continue
                out.append({"enrollment_no": enrollment, "marks": marks, "max_marks": max_marks})
        return out

    def _from_text(self, page):
        out = []
        for line in (page.extract_text() or "").splitlines():
            tokens = line.replace("|", " ").split()
            enr_idx = next((i for i, t in enumerate(tokens) if self._match_enrollment(t)), None)
            if enr_idx is None:
                continue
            marks, max_marks = self._numbers_after(self._rejoin_fraction(tokens[enr_idx + 1:]))
            if marks is None:
                continue
            out.append({"enrollment_no": self._match_enrollment(tokens[enr_idx]),
                        "marks": marks, "max_marks": max_marks})
        return out

    @staticmethod
    def _rejoin_fraction(tokens):
        """['45', '/', '50'] -> ['45/50']"""
        s = " ".join(tokens)
        s = re.sub(r"(\d)\s*/\s*(\d)", r"\1/\2", s)
        return s.split()
