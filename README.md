PII Detector – User Manual


Project Type: Full‑stack (FastAPI backend + React/Vite frontend)
Supported Inputs: Images (PNG/JPG/JPEG), PDF, DOCX
Primary Function: Automatically detect & redact Indian PII in documents/images.


1) One‑Page Concise Overview (How it works)
•	Upload a file (image, PDF, or DOCX) in the web UI.
•	Backend OCR & Rules: For images/PDFs, the backend uses Tesseract OCR to read text, then applies regex & checksum rules to find sensitive items:
o	Aadhaar (with Verhoeff checksum), PAN, mobile numbers, email, VID, Driving Licence, DOB, address keywords + pincode.
•	Redaction:
o	Images/PDF: Draw black rectangles over detected text regions and rebuild a redacted PDF/PNG.
o	DOCX: Replace matched tokens with [REDACTED] and return a new DOCX.
•	Download the redacted output returned by the /redact API.
Pipeline files of interest:
app/main.py (FastAPI) → app/extractor/extractor.py → redactors in app/redactor/* and detectors in app/detector/* → utilities in app/utils/*.










2) Key Features
•	Fast, local redaction of common Indian PII types.
•	Drag‑and‑drop UI with preview (including DOCX preview in browser).
•	Works with multi‑page PDFs (converted to images, processed page‑wise, and re‑assembled).
•	Rule‑based detection you can edit (regex/keywords/checksum).
PII Detected (out of the box): 
o	Aadhaar (12‑digit with Verhoeff) – app/detector/aadhar_card_no.py 
o	PAN – app/detector/pan_card_no.py 
o	Mobile, Email, VID – app/detector/pii.py 
o	Driving Licence – app/detector/driving_licence_no.py 
o	DOB (date formats + validity check) – app/detector/dob.py 
o	Address (keywords + 6‑digit pincode) – app/detector/address.py + app/utils/keyword.py


3) System Requirements
OS: Windows / macOS / Linux
Python: 3.13
Node.js: 22 (for Vite/React frontend)
External binaries: 
•	Tesseract OCR (required)
o	Windows: Install from the official installer.
o	macOS: brew install tesseract 
o	Ubuntu/Debian: sudo apt install tesseract-ocr 
•	Poppler (needed by pdf2image to rasterize PDFs)
o	Windows: Install Poppler for Windows and add bin to PATH. 
o	macOS: brew install poppler 
o	Ubuntu/Debian: sudo apt install poppler-utils
•	Python packages: installed via pip install -r requirements.txt (FastAPI, Uvicorn, python‑multipart, pytesseract, pdf2image, pillow, python‑docx, reportlab, numpy, opencv‑python, etc.).
 If cv2 fails to install, run: pip install opencv-python.

4) Project Structure (simplified)
pii/
├─ pii-detector-backend/
│  ├─ app/
│  │  ├─ main.py                     # FastAPI app & /redact endpoint
│  │  ├─ extractor/
│  │  │  ├─ extractor.py            # Routes by file type (pdf/docx/image)
│  │  │  ├─ pdf_format.py           # PDF → images → redact → PDF
│  │  │  └─ docx_format.py          # Token redaction in DOCX
│  │  ├─ redactor/                  # Redaction routines (image-level)
│  │  ├─ detector/                  # PII detection rules
│  │  └─ utils/                     # regex, keywords, Verhoeff
│  └─ requirements.txt
└─ Pii_detector_frontend/
   ├─ src/App.jsx                   # Upload UI → POST /redact → download
   ├─ index.html, src/main.jsx, src/index.css
   └─ package.json

5) Setup & Installation (Step‑by‑Step)
 A) Backend (FastAPI):-
•	Github Repository Clone
o	https://github.com/PII-Detector/Pii-detector.git
•	Create & activate a virtual env
o	cd pii/pii-detector-backend
o	python -m venv .venv
o	Windows
	.venv\Scripts\activate
o	macOS/Linux
	source .venv/bin/activate
•	Install dependencies
o	pip install --upgrade pip
o	pip install -r requirements.txt
•	Install Tesseract + Poppler (see System Requirements) and ensure they’re on your PATH.
•	Set Tesseract data path
The repo sets TESSDATA_PREFIX in app/main.py to a Windows path:
 	os.environ['TESSDATA_PREFIX'] = r'C:\\Program Files\\Tesseract-OCR\\tessdata\\'
 	Update this for your OS as needed, e.g.:
o	Linux: '/usr/share/tesseract-ocr/5/tessdata/'
o	macOS (Homebrew): '/opt/homebrew/Cellar/tesseract/<ver>/share/tessdata/'
•	Run the API server
o	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
•	CORS: app/main.py allows http://localhost:5173 by default. Add your frontend origin if different.
 B) Frontend (React/Vite)
•	Open a new terminal and run:
o	cd pii/Pii_detector_frontend
o	npm install
o	npm run dev
•	Visit the printed URL (default http://localhost:5173).
•	The upload button will POST to http://localhost:8000/redact as configured in src/App.jsx.
o	To change the API base URL, edit the axios.post("http://localhost:8000/redact", ...) line in App.jsx (or externalize to an env var if desired).

6) Using the App (End‑User Steps)
•	Open the web app (e.g., http://localhost:5173).
•	Click Upload and select a PNG/JPG/JPEG, PDF, or DOCX file.
•	Click Redact (or equivalent action displayed). The frontend sends the file to /redact.
•	Wait for processing; a redacted preview/download button appears.
•	Click Download Redacted File to save the output.
What you get back - Input Image → Output PNG (redacted overlays added) - Input PDF → Output PDF (pages rasterized, redacted, re‑assembled) - Input DOCX → Output DOCX (matched tokens replaced with [REDACTED])

7) API Reference (Minimal)
•	Endpoint: POST /redact
•	Content‑Type: multipart/form-data with file parameter
•	Response: redacted file (binary) with appropriate Content-Type and Content-Disposition.
•	cURL example
o	curl -X POST \
o	-F "file=@/path/to/input.pdf" \
o	http://localhost:8000/redact \
o	-o redacted.pdf

8) Internals & Detection Logic (What happens under the hood)
•	Extractor Router – app/extractor/extractor.py decides by extension:
o	PDF → pdf_format.py: convert each page to an image using pdf2image, run redactors, then rebuild a PDF with reportlab.
o	DOCX → docx_format.py: iterate text runs/paragraphs, mask tokens that match PII → save a new DOCX.
o	Image → call image redactors directly and return a PNG buffer.
•	Redactors (image workflows in app/redactor/*):
o	Preprocess brightness/contrast (PIL/NumPy/OpenCV).
o	pytesseract → get text & bounding boxes.
o	Combine words per line, check detectors.
o	If line contains PII, paint black rectangles over each word box.
•	Detectors (text rules in app/detector/*):
o	Regex for PAN, email, mobile, VID, DL, DOB (app/utils/regex.py).
o	Verhoeff for Aadhaar (app/utils/verhoeff_algorithm.py).
o	Keywords for addresses + pincode match (app/detector/address.py, app/utils/keyword.py).
Signature masking exists as a module (app/redactor/signature.py) but is currently commented out.


9) Configuration & Customization
•	CORS: In app/main.py, adjust origins = ["http://localhost:5173", ...] for your deployment.
•	Tesseract language/data: update TESSDATA_PREFIX to the correct path for your OS/language packs.
•	Regex Rules: edit app/utils/regex.py (e.g., widen/tighten patterns).
•	Address Keywords: edit app/utils/keyword.py (English/Hindi lists).
•	Enable signature redaction: uncomment logic in app/redactor/signature.py and wire it into the pipeline inside app/extractor/extractor.py.
•	Pipeline order: adjust the sequence in app/extractor/extractor.py to run specific redactors earlier/later.

10) Limitations & Notes
•	OCR is not perfect: very low‑quality scans may miss or mis‑locate text → redaction boxes may not align.
•	Rasterization: PDFs are rasterized before redaction; vector text is not edited in‑place.
•	DOCX granularity: word‑level replacement may not preserve exact original formatting in complex documents.
•	Locale: Regex and address keywords are tuned for Indian formats; adapt for other locales.

11) Troubleshooting
•	Tesseract not found / poor OCR: ensure Tesseract is installed and TESSDATA_PREFIX is valid. Try installing language data packs if needed.
•	pdf2image errors: Poppler not installed or not on PATH. Install Poppler and restart shell.
•	cv2 import error: pip install opencv-python (or add to requirements.txt).
•	CORS error in browser: add your frontend origin to origins in app/main.py, restart API.
•	Large PDF is slow: reduce DPI in pdf2image conversion or process pages in batches.

12) Security & Privacy
•	All processing happens on your server. When deployed remotely, enable HTTPS, restrict origins, and consider authentication/rate limiting.
•	Store or log only what you need; avoid persisting uploaded files in production.

13) Extending to New PII Types (Quick Recipe)
•	Create a detector in app/detector/<new_type>.py (regex/logic + test function).
•	Add any keywords/regex in app/utils/*.
•	Wire the detector into an existing image redactor (or make a new one in app/redactor/).
•	Update extractor/extractor.py to call your new redactor.
•	For DOCX, add token‑level checks in docx_format.py.

14) Quick Start Checklist
•	Python 3.10+ and Node 18+ installed
•	Tesseract OCR installed and TESSDATA_PREFIX set
•	Poppler installed and on PATH
•	pip install -r requirements.txt
•	npm install && npm run dev
•	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
•	Open http://localhost:5173 and redact a test file

Appendix: Example Code Pointers
•	POST target in frontend: src/App.jsx (axios to http://localhost:8000/redact).
•	Main API: app/main.py (FastAPI + CORS + /redact).
•	Routing by file type: app/extractor/extractor.py.
•	Regex definitions: app/utils/regex.py.
•	Aadhaar validator: app/utils/verhoeff_algorithm.py.
•	Address keywords: app/utils/keyword.py.
