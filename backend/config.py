import os

from google import genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
UPLOAD_FOLDER = "data/uploads"
FAISS_INDEX_PATH = "data/faiss_index"


def get_genai_client():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Missing Gemini API key. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment."
        )
    return genai.Client(api_key=GEMINI_API_KEY)
