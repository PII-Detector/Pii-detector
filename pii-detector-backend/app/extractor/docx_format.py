import io
from docx import Document
from app.redactor.pii import redact_image_with_pii
from app.redactor.dob import redact_image_with_pii_dob
from app.redactor.address import redact_address_from_image
from app.redactor.aadhar_card_no import redact_image_with_aadhar_card_no
from app.redactor.driving_licence_no import redact_image_with_driving_licence_no

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
