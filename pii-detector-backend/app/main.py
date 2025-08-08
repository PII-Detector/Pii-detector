from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .extractor import redact_file_with_format
import io
import os

# Set TESSDATA_PREFIX for this session
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata\\'

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/redact")
async def redact_file(file: UploadFile = File(...)):
    contents = await file.read()
    redacted_bytes, media_type, extension = redact_file_with_format(file.filename, contents)
    return StreamingResponse(io.BytesIO(redacted_bytes), media_type=media_type, headers={
        "Content-Disposition": f"attachment; filename=redacted.{extension}"
    })
