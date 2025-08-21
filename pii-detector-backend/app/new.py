# def redact_image_with_pii(image_bytes: bytes) -> bytes:
#     # image = Image.open(io.BytesIO(image_bytes))
    
#      # ---- Step 1: Load image ----
#     pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")  # keep RGB
#     np_image = np.array(pil_image)
#     brightness = np.mean(np_image)
#     print(f"Brightness: {brightness}")
#     print(f"Original Resolution: {pil_image.width}x{pil_image.height}")

#     # ---- Step 2: Preprocessing with OpenCV (without forced grayscale output) ----
#     # Convert to OpenCV BGR
#     cv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

#     # Noise reduction
#     cv_image = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)

#     # Convert copy to grayscale ONLY for OCR processing
#     gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

#     # Adaptive threshold (better for scanned docs)
#     image = cv2.adaptiveThreshold(
#         gray, 255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         31, 2
#     )

#     # ---- Step 3: OCR line-level + word-level ----
#     # data = pytesseract.image_to_data(
#     #     thresh, 
#     #     output_type=pytesseract.Output.DICT, 
#     #     config="--oem 1"
#     # )
    
#     # ---- Step 1: Brightness adjustment ----
#     # np_image = np.array(image)
#     # brightness = np.mean(np_image)
#     # print(f"Brightness: {brightness}")
#     # print(f"Original Resolution: {image.width}x{image.height}")

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

#     width, height = image.size
#     draw = ImageDraw.Draw(image)

#     # ---- Step 2: OCR line-level + word-level data ----
#     data = pytesseract.image_to_data(
#         image, 
#         output_type=pytesseract.Output.DICT, 
#         config="--oem 1"
#     )

#     # ---- Step 3: OCR character-level data for DOB redaction ----
#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 1")
#     char_positions = []
#     for box in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = box.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     # ---- Step 4: Group words into lines ----
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

#     # ---- Step 5: Redaction logic ----
#     for line in lines.values():
#         line_text = " ".join(line["text"])
    
#         # Check DOB separately
#         dob_result = detect_pii_dob(line_text)
#         if dob_result["contains_pii_dob"]:
#             print(f"DOB Detected (char-wise): {line_text}")
#             min_x = min([pos[0] for pos in line["positions"]])
#             max_x = max([pos[0] + pos[2] for pos in line["positions"]])
#             min_y = min([pos[1] for pos in line["positions"]])
#             max_y = max([pos[1] + pos[3] for pos in line["positions"]])
#             for ch, cx1, cy1, cx2, cy2 in char_positions:
#                 if (cx1 >= min_x and cx2 <= max_x) and (cy1 >= min_y and cy2 <= max_y):
#                     draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
#             continue  # Skip general PII check if DOB found

#         # General PII detection
#         result = detect_pii(line_text)
#         if result['contains_pii']:
#             print(f"PII Detected in Line: {line_text}")
#             for (x, y, w, h) in line["positions"]:
#                 draw.rectangle([x, y, x + w, y + h], fill="black")


#     # ---- Step 6: Return result ----
#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()