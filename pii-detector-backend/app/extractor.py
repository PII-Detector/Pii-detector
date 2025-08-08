from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from .detector import detect_pii
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
        return redact_image_with_pii(file_bytes), "image/png", "png"
    else:
        raise ValueError("Unsupported file format")
    
    
# def redact_image_with_pii(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
#     width, height = image.size
#     draw = ImageDraw.Draw(image)

#     data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

#     lines = {}
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word and float(data['conf'][i]) > 10:
#             key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
#             if key not in lines:
#                 lines[key] = {
#                     "text": [],
#                     "positions": [],
#                     "raw_words": []
#                 }
#             lines[key]["text"].append(word)
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             lines[key]["positions"].append((x, y, w, h))
#             lines[key]["raw_words"].append((word, x, y, w, h))

#     # Redact full lines with PII
#     for line in lines.values():
#         line_text = " ".join(line["text"])
#         result = detect_pii(line_text)
#         if result['contains_pii']:
#             print(f"🔒 PII Detected in Line: {line_text}")
#             for (x, y, w, h) in line["positions"]:
#                 draw.rectangle([x, y, x + w, y + h], fill="black")
#         else:
#             # Also check each word separately
#             for word, x, y, w, h in line["raw_words"]:
#                 pii_check = detect_pii(word)
#                 if pii_check['contains_pii']:
#                     print(f"🔒 PII Detected in Word: {word}")
#                     draw.rectangle([x, y, x + w, y + h], fill="black")

#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()

from PIL import Image, ImageDraw, ImageEnhance

def redact_image_with_pii(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    
    np_image = np.array(image)
    brightness = np.mean(np_image)
    print(f"Brightness: {brightness}")
    
    # if(brightness >= 199 and brightness <= 205):
    #     data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    # elif(brightness >= 189 and brightness < 199):
    #     enhancer = ImageEnhance.Brightness(image)
    #     image = enhancer.enhance(1.1) # 1.0 = original, >1.0 = brighter, <1.0 = darker
    # elif(brightness >= 179 and brightness < 189):
    #     enhancer = ImageEnhance.Brightness(image)
    #     image = enhancer.enhance(1.1) # 1.0 = original, >1.0 = brighter, <1.0 = darker
    # el
    if(brightness < 179):
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.3) # 1.0 = original, >1.0 = brighter, <1.0 = darker
  

    # Step 1: Adjust brightness
    # enhancer = ImageEnhance.Brightness(image)
    # image = enhancer.enhance(1.3) # 1.0 = original, >1.0 = brighter, <1.0 = darker

    np_image = np.array(image)
    brightness = np.mean(np_image)
    print(f"Brightness: {brightness}")

    width, height = image.size
    draw = ImageDraw.Draw(image)

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    lines = {}
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if word and float(data['conf'][i]) > 10:
            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            if key not in lines:
                lines[key] = {
                    "text": [],
                    "positions": [],
                    "raw_words": []
                }
            lines[key]["text"].append(word)
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            lines[key]["positions"].append((x, y, w, h))
            lines[key]["raw_words"].append((word, x, y, w, h))

    # Redact full lines with PII
    for line in lines.values():
        line_text = " ".join(line["text"])
        result = detect_pii(line_text)
        if result['contains_pii']:
            print(f"PII Detected in Line: {line_text}")
            for (x, y, w, h) in line["positions"]:
                draw.rectangle([x, y, x + w, y + h], fill="black")
        else:
            # Also check each word separately
            for word, x, y, w, h in line["raw_words"]:
                pii_check = detect_pii(word)
                if pii_check['contains_pii']:
                    print(f"PII Detected in Word: {word}")
                    draw.rectangle([x, y, x + w, y + h], fill="black")

    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()


# def redact_image_with_pii(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
    
#     np_image = np.array(image)
#     brightness = np.mean(np_image)
#     print(f"Brightness: {brightness}")
    
#     if(brightness >= 199 & brightness <= 205):
        
        
  

#     # Step 1: Adjust brightness
#     enhancer = ImageEnhance.Brightness(image)
#     image = enhancer.enhance(1.3) # 1.0 = original, >1.0 = brighter, <1.0 = darker

#     np_image = np.array(image)
#     brightness = np.mean(np_image)
#     print(f"Brightness: {brightness}")

#     width, height = image.size
#     draw = ImageDraw.Draw(image)

#     data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

#     lines = {}
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word and float(data['conf'][i]) > 10:
#             key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
#             if key not in lines:
#                 lines[key] = {
#                     "text": [],
#                     "positions": [],
#                     "raw_words": []
#                 }
#             lines[key]["text"].append(word)
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             lines[key]["positions"].append((x, y, w, h))
#             lines[key]["raw_words"].append((word, x, y, w, h))

#     # Redact full lines with PII
#     for line in lines.values():
#         line_text = " ".join(line["text"])
#         result = detect_pii(line_text)
#         if result['contains_pii']:
#             print(f"PII Detected in Line: {line_text}")
#             for (x, y, w, h) in line["positions"]:
#                 draw.rectangle([x, y, x + w, y + h], fill="black")
#         else:
#             # Also check each word separately
#             for word, x, y, w, h in line["raw_words"]:
#                 pii_check = detect_pii(word)
#                 if pii_check['contains_pii']:
#                     print(f"PII Detected in Word: {word}")
#                     draw.rectangle([x, y, x + w, y + h], fill="black")

#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()




# def redact_image_with_pii(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
#     # custom_config = r'--oem 3 --psm 11'
#     data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
#     draw = ImageDraw.Draw(image)

#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if int(data['conf'][i]) > 10 and word:
#             result = detect_pii(word)
#             if result['contains_pii']:
#                 x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#                 draw.rectangle([x, y, x + w, y + h], fill='black')

#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()


# def redact_image_with_pii(image_bytes: bytes) -> bytes:
#     # Load image with PIL
#     image = Image.open(io.BytesIO(image_bytes))

#     # --- OpenCV preprocessing for better OCR ---
#     open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
#     gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
#     thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
#     image = Image.fromarray(thresh)  # Convert back to PIL
#     # -------------------------------------------

#     draw = ImageDraw.Draw(image)
#     custom_config = r'--oem 3 --psm 11'
#     data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=custom_config)

#     lines = {}
#     for i in range(len(data['text'])):
#         if int(data['conf'][i]) > 0 and data['text'][i].strip():
#             line_num = data['line_num'][i]
#             if line_num not in lines:
#                 lines[line_num] = []
#             lines[line_num].append({
#                 'text': data['text'][i],
#                 'left': data['left'][i],
#                 'top': data['top'][i],
#                 'width': data['width'][i],
#                 'height': data['height'][i],
#             })

#     for line in lines.values():
#         line_text = " ".join([w['text'] for w in line])
#         if detect_pii(line_text)['contains_pii']:
#             for w in line:
#                 x, y, w_, h = w['left'], w['top'], w['width'], w['height']
#                 draw.rectangle([x, y, x + w_, y + h], fill='black')

#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()

# def redact_pdf_with_pii(pdf_bytes: bytes) -> bytes:
#     redacted_images = []
#     images = convert_from_bytes(pdf_bytes)

#     for img in images:
#         buf = io.BytesIO()
#         img.save(buf, format="PNG")
#         redacted = redact_image_with_pii(buf.getvalue())
#         redacted_images.append(Image.open(io.BytesIO(redacted)))

#     pdf = FPDF()
#     for img in redacted_images:
#         img_path = "temp.jpg"
#         img.save(img_path)
#         pdf.add_page()
#         pdf.image(img_path, x=0, y=0, w=210, h=297)

#     out_buf = io.BytesIO()
#     pdf_bytes = pdf.output(dest='S').encode('latin1')  # Fix: get string output then encode
#     out_buf.write(pdf_bytes)
#     out_buf.seek(0)
#     return out_buf.read()


def redact_pdf_with_pii(pdf_bytes: bytes) -> bytes:
    redacted_images = []
    images = convert_from_bytes(pdf_bytes)

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        redacted = redact_image_with_pii(buf.getvalue())
        redacted_images.append(Image.open(io.BytesIO(redacted)))

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

# Updated version
# def redact_pdf_with_pii(pdf_bytes: bytes) -> bytes:
#     try:
#         # Convert with higher DPI for better OCR accuracy
#         images = convert_from_bytes(
#             pdf_bytes, 
#             dpi=300, 
#             poppler_path=r'C:\poppler-24.08.0\Library\bin'
#         )
#     except Exception:
#         return pdf_bytes  # Return original on failure
    
#     redacted_images = []
#     for img in images:
#         buf = io.BytesIO()
#         img.save(buf, format="PNG")
#         redacted = redact_image_with_pii(buf.getvalue())
#         redacted_images.append(Image.open(io.BytesIO(redacted)))
    
#     # Create PDF with ReportLab
#     out_buf = io.BytesIO()
#     c = canvas.Canvas(out_buf, pagesize=A4)
    
#     for img in redacted_images:
#         img_width, img_height = img.size
#         aspect = img_height / float(img_width)
#         new_width = A4[0]
#         new_height = new_width * aspect
        
#         img_reader = ImageReader(img)
#         c.drawImage(
#             img_reader, 
#             0, 
#             A4[1] - new_height, 
#             width=new_width, 
#             height=new_height
#         )
#         c.showPage()
    
#     c.save()
#     return out_buf.getvalue()

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
