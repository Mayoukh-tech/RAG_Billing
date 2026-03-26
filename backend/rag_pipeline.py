import numpy as np
import re
from embeddings import create_embeddings
from config import get_genai_client, GEMINI_MODEL


def _token_set(text):
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def retrieve(query, index, chunks, top_k=4):
    if index is None or not chunks:
        return [], []

    query_embedding = np.array(create_embeddings([query]), dtype=np.float32)
    similarities = np.dot(index, query_embedding[0])

    # Hybrid lexical boost helps short factual queries on serverless-friendly retrieval.
    query_tokens = _token_set(query)
    lexical = np.zeros(len(chunks), dtype=np.float32)
    if query_tokens:
        for i, chunk in enumerate(chunks):
            chunk_tokens = _token_set(chunk)
            if chunk_tokens:
                lexical[i] = len(query_tokens & chunk_tokens) / len(query_tokens)

    hybrid_scores = (0.6 * similarities) + (0.4 * lexical)
    k = min(top_k, len(chunks))
    top_indices = np.argsort(hybrid_scores)[::-1][:k]
    scores_arr = hybrid_scores[top_indices]

    results = []
    scores = []
    for idx, score in zip(top_indices, scores_arr):
        if idx < 0:
            continue
        results.append(chunks[idx])
        scores.append(float(score))

    return results, scores


def compute_confidence(scores, answer, context):
    if not scores:
        return 0.0

    # Cosine similarity for normalized vectors is in [0, 1] here.
    similarity = sum(scores) / len(scores)

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

    # Lower threshold because lightweight retrieval scores are smaller than transformer-based scores.
    if max(scores) < 0.08:
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
