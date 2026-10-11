"""
pdf_loader.py
-------------------------------------------------------
PDF Loader without LangChain

Uses PyPDF (pure Python) to extract text
and creates chunks manually.

Author: CampusFlow AI
"""

from pypdf import PdfReader


class Document:
    """
    Simple document object similar to LangChain Document.
    """

    def __init__(self, text):

        self.page_content = text


class PDFLoader:

    def __init__(

        self,

        chunk_size=1000,

        chunk_overlap=200

    ):

        self.chunk_size = chunk_size

        self.chunk_overlap = chunk_overlap

    # =====================================================
    # Load PDF
    # =====================================================

    def load_pdf(self, pdf_path):

        reader = PdfReader(pdf_path)

        documents = []

        for page in reader.pages:

            text = page.extract_text()

            if text:

                documents.append(
                    Document(text)
                )

        return documents

    # =====================================================
    # Split Documents
    # =====================================================

    def split_documents(self, documents):

        chunks = []

        step = self.chunk_size - self.chunk_overlap

        for document in documents:

            text = document.page_content

            start = 0

            while start < len(text):

                end = start + self.chunk_size

                chunk = text[start:end]

                chunks.append(
                    Document(chunk)
                )

                start += step

        return chunks

    # =====================================================
    # Complete Pipeline
    # =====================================================

    def process_pdf(self, pdf_path):

        documents = self.load_pdf(pdf_path)

        chunks = self.split_documents(
            documents
        )

        return {

            "documents": documents,

            "chunks": chunks

        }