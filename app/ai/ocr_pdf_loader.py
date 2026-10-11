from pdf2image import convert_from_path
import pytesseract


class OCRPDFLoader:

    def extract_text(self, pdf_path):

        pages = convert_from_path(pdf_path)

        text = ""

        for page in pages:

            text += pytesseract.image_to_string(page)

            text += "\n"

        return text