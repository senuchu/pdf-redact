from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import fitz  # PyMuPDF
import os
import shutil

app = FastAPI()
UPLOAD_DIR = "/tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def redact_submission_ids(input_pdf, output_pdf):
    """Redacts Submission IDs and 'Document Details' from a PDF."""
    doc = fitz.open(input_pdf)

    for page_num, page in enumerate(doc):
        text_instances = page.search_for("Submission ID trn:oid:::")
        for inst in text_instances:
            rect = fitz.Rect(inst.x0, inst.y0, inst.x1 + 100, inst.y1)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

        if page_num == 0:
            details_instances = page.search_for("Document Details")
            for inst in details_instances:
                rect = fitz.Rect(0, inst.y0 - 50, page.rect.x1, inst.y0)
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

    doc.save(output_pdf)

@app.post("/redact")
async def redact_pdf(file: UploadFile = File(...)):
    """Redacts sensitive information from an uploaded PDF."""
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    output_path = os.path.join(UPLOAD_DIR, f"redacted_{file.filename}")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    redact_submission_ids(input_path, output_path)

    return {"message": "Redaction complete", "redacted_pdf": f"/api/download/redacted_{file.filename}"}

@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """Allows downloading of the redacted PDF."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    return {"error": "File not found"}
