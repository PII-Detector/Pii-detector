import io
from docx import Document
from app.detector.pii import detect_pii
from app.detector.dob import detect_pii_dob
from app.detector.address import detect_pii_address
from app.detector.aadhar_card_no import detect_aadhar_card_no
from app.detector.driving_licence_no import detect_driving_licence_no

def redact_docx_with_pii(docx_bytes: bytes) -> bytes:
    doc = Document(io.BytesIO(docx_bytes))

    for para in doc.paragraphs:
        words = para.text.split()
        new_text = []

        for word in words:
            redacted_word = word

            # Run EVERY detector one by one
            if detect_pii(redacted_word).get("matches"):
                redacted_word = "[REDACTED]"

            if detect_pii_dob(redacted_word).get("matches"):
                redacted_word = "[REDACTED]"

            if detect_pii_address(redacted_word).get("matches"):
                redacted_word = "[REDACTED]"

            if detect_aadhar_card_no(redacted_word).get("contains_aadhar_card_no"):
                redacted_word = "[REDACTED]"

            if detect_driving_licence_no(redacted_word).get("matches"):
                redacted_word = "[REDACTED]"

            new_text.append(redacted_word)

        para.text = " ".join(new_text)

    out_buf = io.BytesIO()
    doc.save(out_buf)
    out_buf.seek(0)
    return out_buf.read()
