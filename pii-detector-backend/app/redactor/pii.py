from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from app.detector.pii import detect_pii
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re



# # ------------------------------------- # 
# # For Pii Detect - Aadhar No, Pan No, DL No

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