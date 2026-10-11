"""
llm.py
-------------------------------------------------------
Loads the Gemini Large Language Model.

Author: CampusFlow AI
"""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_llm():
    """
    Returns a configured Gemini LLM instance.
    """

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in .env file."
        )

    model_name = os.getenv(
        "LLM_MODEL",
        "gemini-3.1-flash-lite"
    )

    print("\n" + "=" * 60)
    print("CampusFlow AI")
    print("=" * 60)
    print(f"Using Gemini Model : {model_name}")
    print("=" * 60 + "\n")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.2,
        google_api_key=api_key,
        max_retries=3,
    )

    return llm