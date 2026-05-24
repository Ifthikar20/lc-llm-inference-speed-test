EXTRACT_QUESTIONS = """You are an exam question writer. Read the study material \
below and generate {n} exam-style multiple-choice questions that test \
understanding of the key concepts.

Return ONLY valid JSON matching this schema, with no extra prose:
{{
  "questions": [
    {{
      "question": "string",
      "options": ["A ...", "B ...", "C ...", "D ..."],
      "answer": "A",
      "explanation": "string"
    }}
  ]
}}

Study material:
---
{material}
---
"""

ANSWER_WITH_CONTEXT = """You are a study assistant. Answer the question using \
ONLY the provided context. If the context does not contain the answer, say so \
plainly instead of guessing.

Context:
---
{context}
---

Question: {question}

Answer:"""
