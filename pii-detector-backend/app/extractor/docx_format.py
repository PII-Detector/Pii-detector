import io
from docx import Document
import re
from app.detector.pii import detect_pii
from app.detector.dob import detect_pii_dob
from app.detector.address import detect_pii_address
from app.detector.aadhar_card_no import detect_aadhar_card_no
from app.detector.driving_licence_no import detect_driving_licence_no
from app.detector.mobile_number import detect_mobile_number


def mask_aadhaar(aadhaar: str) -> str:
    digits = re.sub(r"\D", "", aadhaar)
    if len(digits) == 12:
        return "XXXX XXXX " + digits[-4:]
    return "[REDACTED]"


def mask_mobile(mobile: str) -> str:
    digits = re.sub(r"\D", "", mobile)
    if len(digits) == 10:
        return digits[:2] + "XXXXXX" + digits[-2:]
    elif len(digits) == 12 and digits.startswith("91"):
        return "+91 " + digits[2:4] + "XXXXXX" + digits[-2:]
    return "[REDACTED]"


def redact_docx_with_pii(docx_bytes: bytes) -> bytes:
    doc = Document(io.BytesIO(docx_bytes))

    for para in doc.paragraphs:
        for run in para.runs:
            words = run.text.split()
            new_words = []

            for word in words:
                redacted_word = word

                # Aadhaar
                aadhaar_result = detect_aadhar_card_no(redacted_word)
                if aadhaar_result.get("contains_aadhar_card_no"):
                    redacted_word = mask_aadhaar(word)

                # Mobile
                elif detect_mobile_number(redacted_word).get("matches"):
                    redacted_word = mask_mobile(word)

                # Driving Licence
                elif detect_driving_licence_no(redacted_word).get("matches"):
                    redacted_word = "[REDACTED]"

                # DOB
                elif detect_pii_dob(redacted_word).get("matches"):
                    redacted_word = "[REDACTED]"

                # Address
                elif detect_pii_address(redacted_word).get("matches"):
                    redacted_word = "[REDACTED]"

                # Generic PII
                elif detect_pii(redacted_word).get("matches"):
                    redacted_word = "[REDACTED]"

                new_words.append(redacted_word)

            # Update run text (preserves font, bold, italic, etc.)
            run.text = " ".join(new_words)

    out_buf = io.BytesIO()
    doc.save(out_buf)
    out_buf.seek(0)
    return out_buf.read()
