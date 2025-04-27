from mcpbot.shared.config import COMPANY
from mcpbot.shared.init import config


def rag(question: str) -> str:
    f"""Answers questions using the {COMPANY} knowledge base, with information
    that can be found in the FAQ or Employee handbook.

    Args:
        question: The question to answer.
    """
    db_vector = config.databases.vector["faq"]
    retrieve = db_vector.search(
        question=question,
        method="cosine",
        n_docs=3,
    )
    context = "\n\n".join(retrieve)
    return f"""
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Conversation & Question: {question}
Context: {context}
Answer:
"""
