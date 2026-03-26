import os
import re

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

_model = None


def _get_model():
    global _model
    if _model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(model_name)
    return _model

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
    model = _get_model()
    return model.encode(chunks, normalize_embeddings=True)


def build_faiss_index(embeddings):
    dim = len(embeddings[0])
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(embeddings, dtype=np.float32))
    return index
