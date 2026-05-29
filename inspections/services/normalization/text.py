from datetime import datetime
import re


def normalize_text_value(value):
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("|", "I").replace("0O", "OO")
    return text


def normalize_barcode_value(value):
    text = re.sub(r"\s+", "", normalize_text_value(value)).upper()
    return text


def normalize_manufacturer_value(value):
    text = normalize_text_value(value).upper()
    return text


def normalize_date_value(value):
    text = normalize_text_value(value)
    if not text:
        return ""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        return text


def normalize_ocr_payload(payload):
    payload = payload or {}
    text = normalize_text_value(payload.get("text") or payload.get("raw_text") or "")
    normalized_fields = {
        "medicine_name": normalize_text_value(payload.get("medicine_name")),
        "batch_number": normalize_text_value(payload.get("batch_number")),
        "expiry_date": normalize_date_value(payload.get("expiry_date")),
        "manufacturer": normalize_manufacturer_value(payload.get("manufacturer")),
        "dosage": normalize_text_value(payload.get("dosage")),
        "barcode_data": normalize_barcode_value(payload.get("barcode_data")),
        "regulatory_code": normalize_text_value(payload.get("regulatory_code")).upper(),
    }
    confidence = payload.get("confidence")
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None

    return {
        "provider_name": payload.get("provider_name", "unknown"),
        "text": text,
        "confidence": confidence,
        "normalized_fields": normalized_fields,
        "raw_output": payload.get("raw_output", payload),
        "logs": payload.get("logs", []),
    }
