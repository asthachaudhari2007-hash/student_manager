"""
rag.py
--------------------------------------------------------
Retrieval-Augmented Generation (RAG) Pipeline

Workflow

PDF
    ↓
Extract Text
    ↓
Chunking
    ↓
Embeddings
    ↓
FAISS
    ↓
Retriever
    ↓
Gemini LLM
    ↓
Final Response

Author: CampusFlow AI
"""

from langchain.chains import RetrievalQA

from app.ai.llm import get_llm
from app.ai.pdf_loader import PDFLoader
from app.ai.vector_store import VectorStoreManager


class RAGPipeline:

    def __init__(self, vector_db_path):

        self.vector_db_path = vector_db_path

        self.pdf_loader = PDFLoader()

        self.vector_manager = VectorStoreManager(
            vector_db_path
        )

        self.llm = get_llm()

    # ====================================================
    # Build Vector Database from PDF
    # ====================================================

    def index_pdf(self, pdf_path):

        data = self.pdf_loader.process_pdf(
            pdf_path
        )

        chunks = data["chunks"]

        self.vector_manager.build_vector_store(
            chunks
        )

        return True

    # ====================================================
    # Load Existing Vector Store
    # ====================================================

    def load_vector_store(self):

        return self.vector_manager.load_vector_store()

    # ====================================================
    # Ask Question
    # ====================================================

    def ask(self, question):

        vector_store = self.load_vector_store()

        if vector_store is None:

            return "No vector database found."

        qa = RetrievalQA.from_chain_type(

            llm=self.llm,

            retriever=vector_store.as_retriever(

                search_kwargs={

                    "k": 5

                }

            ),

            return_source_documents=True

        )

        result = qa.invoke(

            {

                "query": question

            }

        )

        return result["result"]

    # ====================================================
    # Retrieve Relevant Documents
    # ====================================================

    def retrieve(self, question):

        vector_store = self.load_vector_store()

        if vector_store is None:

            return []

        docs = vector_store.similarity_search(

            question,

            k=5

        )

        return docs