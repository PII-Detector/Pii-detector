from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from .detector import detect_pii, detect_pii_dob, detect_pii_address
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np

def redact_file_with_format(filename: str, file_bytes: bytes):
    ext = filename.lower().split('.')[-1]
    if ext == "pdf":
        return redact_pdf_with_pii(file_bytes), "application/pdf", "pdf"
    elif ext == "docx":
        return redact_docx_with_pii(file_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"
    elif ext in ["png", "jpg", "jpeg"]:
        processed_image = redact_image_with_pii_dob(file_bytes)
        processed_image = redact_image_with_pii(processed_image)
        processed_image = redact_address_from_image(processed_image)
        # processed_image = redact_pincode_from_image(processed_image)
        return processed_image, "image/png", "png"
    else:
        raise ValueError("Unsupported file format")




# ------------------------------------- # 
# For Pii Detect - Aadhar No, Pan No, DL No

def redact_image_with_pii(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # ---- Step 2: OCR line-level + word-level data ----
    data = pytesseract.image_to_data(
        image, 
        output_type=pytesseract.Output.DICT, 
        config="--oem 1"
    )

    char_boxes = pytesseract.image_to_boxes(image, config="--oem 1")
    char_positions = []
    for box in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = box.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    lines = {}
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if word and float(data['conf'][i]) > 10:
            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            if key not in lines:
                lines[key] = {"text": [], "positions": [], "raw_words": []}
            lines[key]["text"].append(word)
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            lines[key]["positions"].append((x, y, w, h))
            lines[key]["raw_words"].append((word, x, y, w, h))


    for line in lines.values():
        line_text = " ".join(line["text"])
     
        result = detect_pii(line_text)
        if result['contains_pii']:
            print(f"PII Detected in Line: {line_text}")
            for (x, y, w, h) in line["positions"]:
                draw.rectangle([x, y, x + w, y + h], fill="black")

    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()

# ---- Image Redactor (Only Address) ----
def redact_address_from_image(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # OCR with word-level positions
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 1"
    )

    # Group into lines
    lines = {}
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if word and float(data['conf'][i]) > 10:
            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            if key not in lines:
                lines[key] = {"text": [], "positions": []}
            lines[key]["text"].append(word)
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            lines[key]["positions"].append((x, y, w, h))

    # 🔹 Detect and redact addresses
    for line in lines.values():
        line_text = " ".join(line["text"])
        result = detect_pii_address(line_text)

        if result['contains_pii_address']:
            print(f"[ADDRESS REDACTED] {line_text}")
            for (x, y, w, h) in line["positions"]:
                draw.rectangle([x, y, x + w, y + h], fill="black")

    # Return processed image
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()

# ----------------------------------------------- #
# this redacts only dob in character form

def redact_image_with_pii_dob(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))

    # Brightness adjustment
    np_image = np.array(image)
    brightness = np.mean(np_image)
    print(f"Brightness: {brightness}")
    print(f"Original Resolution: {image.width}x{image.height}")

    enhancer = ImageEnhance.Brightness(image)
    if 175 <= brightness < 179:
        image = enhancer.enhance(1.1)
    elif brightness < 179:
        image = enhancer.enhance(1.3)
    elif 205 <= brightness <= 215:
        image = enhancer.enhance(0.95)
    elif 215 < brightness <= 225:
        image = enhancer.enhance(0.9)
    elif brightness > 225:
        image = enhancer.enhance(0.85)

    np_image = np.array(image)
    brightness = np.mean(np_image)
    print(f"New Brightness: {brightness}")

    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Get line-level OCR data
    data = pytesseract.image_to_data(
        image, 
        output_type=pytesseract.Output.DICT, 
        config="--oem 1"
    )

    # Get all character boxes
    char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
    char_positions = []
    for b in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = b.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        # Convert coordinates
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    # Loop through OCR lines
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if text and float(data['conf'][i]) > 10:
            if detect_pii_dob(text)['contains_pii_dob']:
                print(f"PII DOB Detected in Line: {text}")
                # Bounding box for this line
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                # Redact all characters inside this line's bounding box
                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (cx1 >= x and cx2 <= x + w) and (cy1 >= y and cy2 <= y + h):
                        draw.rectangle([cx1, cy1, cx2, cy2], fill="black")

    # Save and return
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()

def redact_pdf_with_pii(pdf_bytes: bytes) -> bytes:
    redacted_images = []
    images = convert_from_bytes(pdf_bytes)

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        redacted_pii = redact_image_with_pii_dob(buf.getvalue())
        redacted_pii = redact_image_with_pii(redacted_pii)
        redacted_images.append(Image.open(io.BytesIO(redacted_pii)))

    out_buf = io.BytesIO()
    c = canvas.Canvas(out_buf, pagesize=A4)

    for img in redacted_images:
        img_width, img_height = img.size
        aspect = img_height / float(img_width)
        new_width = A4[0]
        new_height = new_width * aspect

        img_reader = ImageReader(img)
        c.drawImage(img_reader, 0, A4[1] - new_height, width=new_width, height=new_height)
        c.showPage()

    c.save()
    out_buf.seek(0)
    return out_buf.read()

def redact_docx_with_pii(docx_bytes: bytes) -> bytes:
    doc = Document(io.BytesIO(docx_bytes))
    for para in doc.paragraphs:
        for word in para.text.split():
            if detect_pii(word)['matches']:
                para.text = para.text.replace(word, "[REDACTED]")

    out_buf = io.BytesIO()
    doc.save(out_buf)
    out_buf.seek(0)
    return out_buf.read()
