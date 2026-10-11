from langchain_core.prompts import ChatPromptTemplate


STUDENT_EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""

You are an expert data extractor.

Extract every student's information from the document.

Return ONLY valid JSON.

Format:

[
{
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
}
]

Do not include explanations.

Document:

{context}

""")