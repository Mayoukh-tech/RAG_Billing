from config import get_genai_client, GEMINI_MODEL
import json
import re

EXPECTED_FIELDS = [
    "shipment_id",
    "shipper",
    "consignee",
    "pickup_datetime",
    "delivery_datetime",
    "equipment_type",
    "mode",
    "rate",
    "currency",
    "weight",
    "carrier_name",
]


def _extract_json_from_text(text):
    if not text:
        return {"error": "Empty extraction response"}

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {"raw_output": text, "error": "Model did not return valid JSON"}


def _normalize_extraction_payload(payload):
    if not isinstance(payload, dict):
        return {field: None for field in EXPECTED_FIELDS}

    normalized = {}
    for field in EXPECTED_FIELDS:
        value = payload.get(field, None)

        if field == "rate" and value is not None:
            if isinstance(value, str):
                numeric = value.replace(",", "").strip()
                try:
                    value = float(numeric) if "." in numeric else int(numeric)
                except ValueError:
                    value = None
            elif not isinstance(value, (int, float)):
                value = None

        normalized[field] = value

    return normalized


def extract_data(text):

    prompt = """
You are an expert logistics document parser.

Your task is to extract structured shipment data from the document.

IMPORTANT RULES:
- Return ONLY valid JSON (no explanations, no markdown)
- Do NOT hallucinate values
- If a field is missing, return null
- If multiple values exist, choose the most relevant shipment-level value
- Dates must be in ISO format: YYYY-MM-DD HH:MM (if time exists)
- Numbers should be clean (no commas, include units where applicable)

FIELD DEFINITIONS:
- shipment_id: Reference ID or Load ID
- shipper: Pickup company/location name
- consignee: Delivery company/location name
- pickup_datetime: Pickup date + time
- delivery_datetime: Delivery date + time
- equipment_type: e.g., Flatbed, Reefer, Dry Van
- mode: e.g., FTL, LTL, Truckload
- rate: numeric value only
- currency: e.g., USD
- weight: include units (e.g., "56000 lbs")
- carrier_name: Carrier company name

SPECIAL HANDLING:
- Tables may contain key data (e.g., weight, commodity)
- "Pickup" section maps to shipper
- "Drop" section maps to consignee
- "Carrier Details" maps to carrier_name, equipment_type, rate
- "Rate Breakdown" maps to rate and currency

OUTPUT FORMAT:
{
  "shipment_id": string or null,
  "shipper": string or null,
  "consignee": string or null,
  "pickup_datetime": string or null,
  "delivery_datetime": string or null,
  "equipment_type": string or null,
  "mode": string or null,
  "rate": number or null,
  "currency": string or null,
  "weight": string or null,
  "carrier_name": string or null
}

DOCUMENT:
""" + text

    client = get_genai_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    try:
        parsed = _extract_json_from_text(response.text)
        return _normalize_extraction_payload(parsed)
    except Exception as e:
        return {"error": f"Extraction failed: {e}"}
