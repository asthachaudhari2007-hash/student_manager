"""
vector_store.py
----------------------------------------------------
FAISS Vector Store Manager

Creates, saves, loads and searches
the vector database used for RAG.

Author: CampusFlow AI
"""

import os

from langchain_community.vectorstores import FAISS

from app.ai.embeddings import EmbeddingManager


class VectorStoreManager:

    def __init__(self, vector_db_path):

        self.vector_db_path = vector_db_path

        self.embeddings = (
            EmbeddingManager()
            .get_embeddings()
        )

    # =====================================================
    # Create Vector Store
    # =====================================================

    def create_vector_store(self, chunks):

        if not chunks:
            raise ValueError(
                "No document chunks were provided."
            )

        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )

        return vector_store

    # =====================================================
    # Save Vector Store
    # =====================================================

    def save_vector_store(self, vector_store):

        os.makedirs(
            self.vector_db_path,
            exist_ok=True
        )

        vector_store.save_local(
            self.vector_db_path
        )

    # =====================================================
    # Load Vector Store
    # =====================================================

    def load_vector_store(self):

        if not os.path.exists(self.vector_db_path):

            return None

        try:

            vector_store = FAISS.load_local(

                self.vector_db_path,

                self.embeddings,

                allow_dangerous_deserialization=True

            )

            return vector_store

        except Exception as e:

            print(f"Error loading vector store: {e}")

            return None

    # =====================================================
    # Build Vector Store
    # =====================================================

    def build_vector_store(self, chunks):

        vector_store = self.create_vector_store(
            chunks
        )

        self.save_vector_store(
            vector_store
        )

        return vector_store

    # =====================================================
    # Similarity Search
    # =====================================================

    def search(

        self,

        query,

        k=5

    ):

        vector_store = self.load_vector_store()

        if vector_store is None:

            return []

        try:

            results = vector_store.similarity_search(

                query,

                k=k

            )

            return results

        except Exception as e:

            print(f"Search Error: {e}")

            return []

    # =====================================================
    # Delete Vector Store
    # =====================================================

    def delete_vector_store(self):

        if not os.path.exists(self.vector_db_path):

            return

        for file in os.listdir(self.vector_db_path):

            os.remove(

                os.path.join(

                    self.vector_db_path,

                    file

                )

            )

        print("Vector database deleted successfully.")