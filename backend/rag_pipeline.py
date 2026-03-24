import numpy as np
from embeddings import create_embeddings
from config import get_genai_client, GEMINI_MODEL

def retrieve(query, index, chunks, top_k=4):
    if index is None or not chunks:
        return [], []

    query_embedding = np.array(create_embeddings([query]), dtype=np.float32)
    k = min(top_k, len(chunks))
    scores_arr, indices = index.search(query_embedding, k)

    results = []
    scores = []
    for idx, score in zip(indices[0], scores_arr[0]):
        if idx < 0:
            continue
        results.append(chunks[idx])
        scores.append(float(score))

    return results, scores


def compute_confidence(scores, answer, context):
    if not scores:
        return 0.0

    # Cosine similarity from IndexFlatIP is in [-1, 1]; map it to [0, 1].
    similarity = (sum(scores) / len(scores) + 1) / 2

    overlap = len(set(answer.split()) & set(context.split()))
    coverage = overlap / max(len(answer.split()), 1)

    return round(0.6 * similarity + 0.4 * coverage, 2)


def ask_question(query, index, chunks):
    if index is None or not chunks:
        return {
            "answer": "Please upload a document first.",
            "sources": [],
            "confidence": 0.0,
        }

    docs, scores = retrieve(query, index, chunks)
    if not docs:
        return {
            "answer": "Not found in document",
            "sources": [],
            "confidence": 0.0,
        }

    # Guardrail: practical threshold for cosine similarity in this setup.
    if max(scores) < 0.25:
        return {
            "answer": "Not found in document",
            "sources": [],
            "confidence": 0.2,
        }

    context = "\n".join(docs)

    prompt = f"""
    You are a logistics AI assistant.

    Answer ONLY using the context below.
    If not found, say "Not found in document".

    Context:
    {context}

    Question:
    {query}
    """

    client = get_genai_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    answer = (response.text or "").strip()
    if not answer:
        answer = "Not found in document"

    confidence = compute_confidence(scores, answer, context)

    return {
        "answer": answer,
        "sources": docs,
        "confidence": confidence,
    }
