DIFFICULTY_GUIDE = {
    "easy": "Make them straightforward recall questions a beginner can answer "
    "directly from the text.",
    "medium": "Make them require understanding of the concepts, not just recall.",
    "hard": "Make them challenging: require synthesis across multiple facts, "
    "include plausible distractors, and test deeper reasoning.",
    "exam": "Write rigorous, exam-grade questions with subtle, plausible "
    "distractors that test application and analysis of the concepts, not "
    "mere recall. Avoid giving away the answer through wording.",
}

EXTRACT_QUESTIONS = """You are an exam question writer. Read the study material \
below and generate {n} exam-style multiple-choice questions that test \
understanding of the key concepts.

Difficulty: {difficulty_label}. {difficulty_guide}

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
