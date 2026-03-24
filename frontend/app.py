import requests
import streamlit as st

st.title("Ultra Doc Intelligence")

backend_url = "http://127.0.0.1:5000"

uploaded_file = st.file_uploader("Upload Logistics Document")

if st.button("Upload") and uploaded_file:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    try:
        response = requests.post(f"{backend_url}/upload", files=files, timeout=60)
        try:
            payload = response.json()
        except ValueError:
            st.error("Backend returned a non-JSON response during upload.")
            st.text(response.text[:500])
            st.stop()
        if response.ok:
            st.success(payload.get("message", "Upload completed"))
        else:
            st.error(payload.get("error", payload.get("message", "Upload failed")))
    except requests.RequestException as e:
        st.error(f"Backend unreachable: {e}")

query = st.text_input("Ask a question")

if st.button("Ask"):
    if not query.strip():
        st.warning("Please enter a question first.")
    else:
        try:
            response = requests.post(
                f"{backend_url}/ask",
                json={"query": query},
                timeout=90,
            )
            try:
                res = response.json()
            except ValueError:
                st.error("Backend returned a non-JSON response.")
                st.text(response.text[:500])
                st.stop()

            answer = res.get("answer")
            confidence = res.get("confidence", 0)
            sources = res.get("sources", [])
            error = res.get("error")

            st.write("### Answer")
            if answer is not None:
                st.write(answer)
            else:
                st.write("No answer available.")

            st.write("### Confidence")
            st.write(confidence)

            st.write("### Sources")
            if sources:
                for i, s in enumerate(sources, start=1):
                    source_text = str(s).strip()
                    preview = source_text[:220] + ("..." if len(source_text) > 220 else "")
                    with st.expander(f"Source {i}: {preview}"):
                        st.write(source_text)
            else:
                st.write("No sources returned.")

            if not response.ok or error:
                st.error(error or f"Request failed with status {response.status_code}")
        except requests.RequestException as e:
            st.error(f"Backend request failed: {e}")

if st.button("Extract Structured Data"):
    try:
        response = requests.post(f"{backend_url}/extract", timeout=90)
        payload = response.json()
        if response.ok:
            st.json(payload.get("data", {}))
        else:
            st.error(payload.get("error", "Extraction failed"))
    except requests.RequestException as e:
        st.error(f"Backend request failed: {e}")
