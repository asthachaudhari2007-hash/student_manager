"""
embeddings.py
------------------------------------------------
Embedding Manager

Uses Google's Gemini Embedding Model for
Retrieval-Augmented Generation (RAG).

Author: CampusFlow AI
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()


class EmbeddingManager:
    """
    Creates and returns Google Gemini embeddings.
    """

    def __init__(self):

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in .env file."
            )

        model = os.getenv(
            "EMBEDDING_MODEL",
            "models/gemini-embedding-001"
        )

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key
        )

    # =====================================================
    # Return Embedding Object
    # =====================================================

    def get_embeddings(self):
        return self.embeddings