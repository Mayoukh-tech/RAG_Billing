import re

import numpy as np

def chunk_text(text, chunk_size=500, overlap_words=25):

    text = re.sub(r'\s+', ' ', text).strip()

    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            current_chunk = current_chunk.strip()
            if current_chunk:
                chunks.append(current_chunk)

            # Word-based overlap keeps boundaries readable
            overlap_tokens = current_chunk.split()[-overlap_words:]
            overlap_text = " ".join(overlap_tokens)
            current_chunk = (overlap_text + " " + sentence).strip() + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def create_embeddings(chunks):
    """
    Lightweight hashed bag-of-words embeddings for serverless environments.
    Keeps dependencies small enough for Vercel Lambda limits.
    """
    if not chunks:
        return np.zeros((0, 768), dtype=np.float32)

    dim = 768
    vectors = np.zeros((len(chunks), dim), dtype=np.float32)

    for i, text in enumerate(chunks):
        tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
        for token in tokens:
            idx = hash(token) % dim
            vectors[i, idx] += 1.0

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    vectors = vectors / norms
    return vectors


def build_faiss_index(embeddings):
    # Retained function name to avoid changing app imports.
    if embeddings is None:
        return None
    return np.array(embeddings, dtype=np.float32)
