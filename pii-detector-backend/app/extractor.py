from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from .detector import detect_pii, detect_pii_dob, detect_pii_address, detect_signature_keywords, detect_aadhar_card_no, detect_driving_licence_no
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re

def redact_file_with_format(filename: str, file_bytes: bytes):
    ext = filename.lower().split('.')[-1]
    if ext == "pdf":
        return redact_pdf_with_pii(file_bytes), "application/pdf", "pdf"
    elif ext == "docx":
        return redact_docx_with_pii(file_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"
    elif ext in ["png", "jpg", "jpeg"]:
        processed_image = redact_image_with_pii_dob(file_bytes)
        processed_image = redact_image_with_aadhar_card_no(processed_image)
        processed_image = redact_image_with_pii(processed_image)
        processed_image = redact_address_from_image(processed_image)
        # processed_image = redact_signatures_from_image(processed_image)
        return processed_image, "image/png", "png"
    else:
        raise ValueError("Unsupported file format")


# ------------------------------------------ #
# For Aadhar Card
# def redact_image_with_aadhar_card_no(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
#     draw = ImageDraw.Draw(image)
#     width, height = image.size

#     # ---- Step 2: OCR line-level + word-level data ----
#     data = pytesseract.image_to_data(
#         image, 
#         output_type=pytesseract.Output.DICT, 
#         config="--oem 1"
#     )

#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 1")
#     char_positions = []
#     for box in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = box.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     lines = {}
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word and float(data['conf'][i]) > 10:
#             key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
#             if key not in lines:
#                 lines[key] = {"text": [], "positions": [], "raw_words": []}
#             lines[key]["text"].append(word)
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             lines[key]["positions"].append((x, y, w, h))
#             lines[key]["raw_words"].append((word, x, y, w, h))


#     for line in lines.values():
#         line_text = " ".join(line["text"])
     
#         result = detect_aadhar_card_no(line_text)
#         if result['contains_aadhar_card_no']:
#             print(f"Aadhar Card No Detected in Line: {line_text}")
#             for (x, y, w, h) in line["positions"]:
#                 draw.rectangle([x, y, x + w, y + h], fill="black")

#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()

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

# ------------------------------------ # 
# aadhar card no redactor based on character 

# def redact_image_with_aadhar_card_no(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
#     draw = ImageDraw.Draw(image)
#     width, height = image.size

#     # OCR line-level data
#     data = pytesseract.image_to_data(
#         image,
#         output_type=pytesseract.Output.DICT,
#         config="--oem 1"
#     )

#     # OCR character boxes
#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
#     char_positions = []
#     for box in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = box.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     # Group OCR results by line
#     lines = {}
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word and float(data['conf'][i]) > 10:
#             key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
#             if key not in lines:
#                 lines[key] = {"text": [], "positions": [], "raw_words": []}
#             lines[key]["text"].append(word)
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             lines[key]["positions"].append((x, y, w, h))
#             lines[key]["raw_words"].append((word, x, y, w, h))

#     # Redact Aadhaar digits character-wise
#     for line in lines.values():
#         line_text = " ".join(line["text"])
#         result = detect_aadhar_card_no(line_text)
#         if result['contains_aadhar_card_no']:
#             print(f"Aadhar Card No Detected in Line: {line_text}")

#             for pii in result['aadhar_card_no_details']:
#                 aadhar_value = re.sub(r'\D', '', pii['value'])  # only digits
#                 redacted_value = ""
#                 target_index = 0
#                 # max_redact = len(aadhar_value)  # change to 8 if you want only first 8 digits
#                 max_redact = 8

#                 # Iterate over all character boxes
#                 for ch, cx1, cy1, cx2, cy2 in char_positions:
#                     if target_index < max_redact and ch == aadhar_value[target_index]:
#                         draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
#                         redacted_value += ch
#                         target_index += 1

#                 print(f"Redacted Aadhaar digits: {redacted_value}")

#     # Save image to bytes
#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()

# ----------------------------------------------- #
# Aadhar card no redactor based on character - with 8 digits complete working

def redact_image_with_aadhar_card_no(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # OCR line-level data
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 1"
    )

    # Group OCR results by line
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

    # Now get character boxes once
    char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
    char_positions = []
    for box in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = box.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    # Process each line
    for line in lines.values():
        line_text = " ".join(line["text"])
        result = detect_aadhar_card_no(line_text)

        if result['contains_aadhar_card_no']:
            print(f"Aadhar Card No Detected in Line: {line_text}")

            # Find bounding box for this line
            min_x = min(p[0] for p in line["positions"])
            min_y = min(p[1] for p in line["positions"])
            max_x = max(p[0] + p[2] for p in line["positions"])
            max_y = max(p[1] + p[3] for p in line["positions"])

            for pii in result['aadhar_card_no_details']:
                aadhar_value = re.sub(r'\D', '', pii['value'])  # only digits
                target_index = 0
                max_redact = 8  # redact first 8 digits (change if needed)

                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (
                        target_index < max_redact
                        and ch.isdigit()
                        and cx1 >= min_x and cx2 <= max_x and cy1 >= min_y and cy2 <= max_y
                        and ch == aadhar_value[target_index]
                    ):
                        draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                        target_index += 1

    # Save image to bytes
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()

def redact_image_with_driving_licence_no(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # OCR line-level data
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 1"
    )

    # Group OCR results by line
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

    # Now get character boxes once
    char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
    char_positions = []
    for box in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = box.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    # Process each line
    for line in lines.values():
        line_text = " ".join(line["text"])
        result = detect_driving_licence_no(line_text)

        if result['contains_aadhar_card_no']:
            print(f"Driving Licence No Detected in Line: {line_text}")

            # Find bounding box for this line
            min_x = min(p[0] for p in line["positions"])
            min_y = min(p[1] for p in line["positions"])
            max_x = max(p[0] + p[2] for p in line["positions"])
            max_y = max(p[1] + p[3] for p in line["positions"])

            for pii in result['driving_licence_no_details']:
                aadhar_value = re.sub(r'\D', '', pii['value'])  # only digits
                target_index = 0
                max_redact = 8  # redact first 8 digits (change if needed)

                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (
                        target_index < max_redact
                        and ch.isdigit()
                        and cx1 >= min_x and cx2 <= max_x and cy1 >= min_y and cy2 <= max_y
                        and ch == aadhar_value[target_index]
                    ):
                        draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                        target_index += 1

    # Save image to bytes
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
# this redacts only dob in character form for day,month,year

# def redact_image_with_pii_dob(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))

#     # Brightness adjustment
#     np_image = np.array(image)
#     brightness = np.mean(np_image)
#     print(f"Brightness: {brightness}")
#     print(f"Original Resolution: {image.width}x{image.height}")

#     enhancer = ImageEnhance.Brightness(image)
#     if 175 <= brightness < 179:
#         image = enhancer.enhance(1.1)
#     elif brightness < 179:
#         image = enhancer.enhance(1.3)
#     elif 205 <= brightness <= 215:
#         image = enhancer.enhance(0.95)
#     elif 215 < brightness <= 225:
#         image = enhancer.enhance(0.9)
#     elif brightness > 225:
#         image = enhancer.enhance(0.85)

#     np_image = np.array(image)
#     brightness = np.mean(np_image)
#     print(f"New Brightness: {brightness}")

#     draw = ImageDraw.Draw(image)
#     width, height = image.size

#     # Get line-level OCR data
#     data = pytesseract.image_to_data(
#         image, 
#         output_type=pytesseract.Output.DICT, 
#         config="--oem 1"
#     )

#     # Get all character boxes
#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
#     char_positions = []
#     for b in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = b.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         # Convert coordinates
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     # Loop through OCR lines
#     n_boxes = len(data['level'])
#     for i in range(n_boxes):
#         text = data['text'][i].strip()
#         if text and float(data['conf'][i]) > 10:
#             if detect_pii_dob(text)['contains_pii_dob']:
#                 print(f"PII DOB Detected in Line: {text}")
#                 # Bounding box for this line
#                 x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#                 # Redact all characters inside this line's bounding box
#                 for ch, cx1, cy1, cx2, cy2 in char_positions:
#                     if (cx1 >= x and cx2 <= x + w) and (cy1 >= y and cy2 <= y + h):
#                         draw.rectangle([cx1, cy1, cx2, cy2], fill="black")

#     # Save and return
#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()

# --------------------------------------------- #
# this redacts only dob based on character - day, month
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

    # OCR line-level
    data = pytesseract.image_to_data(
        image, 
        output_type=pytesseract.Output.DICT, 
        config="--oem 1"
    )

    # OCR character-level
    char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
    char_positions = []
    for b in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = b.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    # Loop through OCR lines
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if text and float(data['conf'][i]) > 10:
            dob_result = detect_pii_dob(text)
            if dob_result['contains_pii_dob']:
                print(f"PII DOB Detected in Line: {text}")

                # Bounding box of this line
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                # Take first DOB match (if multiple)
                dob_details = dob_result['dob_details'][0]
                dob_day = str(dob_details.get("day", "")).zfill(2)
                dob_month = str(dob_details.get("month", "")).zfill(2)
                print(f"Details: {dob_details} Date: {dob_day} Month: {dob_month}")

               # Store redacted chars for debug
                redacted_value = ""
                redacted_count = 0

                # Redact only day + month chars
                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (cx1 >= x and cx2 <= x + w) and (cy1 >= y and cy2 <= y + h):
                        if redacted_count < 5:
                            draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                            redacted_value += ch   # collect the char
                            redacted_count += 1

                if redacted_value:
                    print(f"Redacted DOB part: {redacted_value} , {redacted_count}")

    # Save & return
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()


def redact_signatures_from_image(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    np_img = np.array(image)

    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    draw = ImageDraw.Draw(image)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # basic size heuristic
        if not (50 < w < 600 and 20 < h < 200 and w > h):
            continue

        sig_crop = image.crop((x, y, x + w, y + h))
        text_in_region = pytesseract.image_to_string(sig_crop).strip()

        # ✅ Use your signature keyword detector
        keyword_check = detect_signature_keywords(text_in_region)

        # Skip if text is clean normal text without signature keywords
        if text_in_region and not keyword_check["contains_signature_keyword"]:
            continue

        # Otherwise redact
        print(f"[SIGNATURE REDACTED] at (x={x}, y={y}, w={w}, h={h}) | OCR guess: '{text_in_region}'")
        draw.rectangle([x, y, x + w, y + h], fill="black")

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# def redact_signatures_from_image(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     np_img = np.array(image)

#     gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
#     _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
#     morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

#     contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     draw = ImageDraw.Draw(image)

#     for cnt in contours:
#         x, y, w, h = cv2.boundingRect(cnt)
#         # signature heuristic: wider than tall, not too small, not huge
#         if 50 < w < 600 and 20 < h < 200 and w > h:
#             # Extract possible signature region for logging
#             sig_crop = image.crop((x, y, x + w, y + h))

#             # Run OCR inside the suspected signature region
#             text_in_region = pytesseract.image_to_string(sig_crop).strip()

#             # Print log in console
#             print(f"[SIGNATURE REDACTED] at (x={x}, y={y}, w={w}, h={h}) | OCR guess: '{text_in_region}'")
#             draw.rectangle([x, y, x+w, y+h], fill="black")


#     buf = io.BytesIO()
#     image.save(buf, format="PNG")
#     buf.seek(0)
#     return buf.read()

def redact_pdf_with_pii(pdf_bytes: bytes) -> bytes:
    redacted_images = []
    images = convert_from_bytes(pdf_bytes)

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        redacted_pii = redact_image_with_pii_dob(buf.getvalue())
        redacted_pii = redact_image_with_pii(redacted_pii)
        redacted_pii = redact_address_from_image(redacted_pii)
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
