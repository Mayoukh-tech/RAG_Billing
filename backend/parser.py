import pdfplumber
import docx
import os
import re


def _extract_pdf_text_with_word_gaps(file_path):
    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=True)
            if not words:
                page_text = page.extract_text() or ""
                pages_text.append(page_text)
                continue

            # Group words by approximate row, then rebuild each row with spaces.
            rows = {}
            for w in words:
                row_key = round(float(w.get("top", 0.0)), 1)
                rows.setdefault(row_key, []).append(w)

            row_texts = []
            for row_key in sorted(rows.keys()):
                row_words = sorted(rows[row_key], key=lambda x: float(x.get("x0", 0.0)))
                row_line = " ".join(str(w.get("text", "")).strip() for w in row_words if w.get("text"))
                if row_line:
                    row_texts.append(row_line)

            pages_text.append("\n".join(row_texts))

    return "\n\n".join(pages_text)


def clean_text(text):
    # Reinsert likely missing boundaries from PDF extraction artifacts.
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)

    # Preserve word boundaries; only normalize excessive whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    text = ""
    
    if ext == ".pdf":
        try:
            text = _extract_pdf_text_with_word_gaps(file_path)

        except Exception as e:
            print("pdfplumber failed, fallback to pypdf:", e)

            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])

    # DOCX
    elif ext == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])

    # TEXT FILES
    elif ext in {".txt", ".md", ".csv", ".json"}:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext or 'unknown'}")

    text = clean_text(text)

    return text
