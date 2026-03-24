from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

from parser import parse_document
from embeddings import chunk_text, create_embeddings, build_faiss_index
from rag_pipeline import ask_question
from extractor import extract_data

app = Flask(__name__)
CORS(app)

chunks_store = []
faiss_index = None
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "data", "uploads")


@app.route("/upload", methods=["POST"])
def upload():
    try:
        global chunks_store, faiss_index

        if "file" not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "No file selected"}), 400

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_DIR, filename)
        file.save(path)

        text = parse_document(path)
        if not text.strip():
            return jsonify({"error": "No readable text found in the document"}), 400

        chunks = chunk_text(text)
        if not chunks:
            return jsonify({"error": "Failed to create text chunks from document"}), 400

        embeddings = create_embeddings(chunks)
        faiss_index = build_faiss_index(embeddings)
        chunks_store = chunks

        return jsonify({
            "message": "Document processed successfully",
            "chunks": len(chunks),
            "filename": filename
        })
    except Exception as e:
        print("UPLOAD ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()

        if not data or "query" not in data:
            return jsonify({
                "answer": None,
                "confidence": 0,
                "sources": [],
                "error": "Missing query"
            }), 400

        query = data["query"]

        result = ask_question(query, faiss_index, chunks_store)

        # 👇 normalize result
        return jsonify({
            "answer": result.get("answer", str(result)),
            "confidence": result.get("confidence", 0.0),
            "sources": result.get("sources", [])
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "answer": None,
            "confidence": 0,
            "sources": [],
            "error": str(e)
        }), 500

@app.route("/extract", methods=["POST"])
def extract():
    try:
        if not chunks_store:
            return jsonify({"error": "No uploaded document found. Upload a file first."}), 400

        full_text = "\n".join(chunks_store)
        result = extract_data(full_text)

        return jsonify({"data": result})
    except Exception as e:
        print("EXTRACT ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
