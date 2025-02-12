import io
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse

app = FastAPI()

def redact_submission_ids(input_pdf: io.BytesIO) -> io.BytesIO:
    """Redacts Submission IDs and 'Document Details' from a PDF."""
    doc = fitz.open(input_pdf)

    for page_num, page in enumerate(doc):
        # Redact Submission IDs
        text_instances = page.search_for("Submission ID trn:oid:::")
        for inst in text_instances:
            rect = fitz.Rect(inst.x0, inst.y0, inst.x1 + 100, inst.y1)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # White rectangle

        # If it's the first page, redact "Document Details"
        if page_num == 0:
            details_instances = page.search_for("Document Details")
            for inst in details_instances:
                rect = fitz.Rect(0, inst.y0 - 50, page.rect.x1, inst.y0)  # Extend the width fully
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # White rectangle

    # Save the redacted PDF to an in-memory byte stream (BytesIO)
    output_pdf = io.BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)  # Rewind the BytesIO stream to the beginning
    return output_pdf

@app.post("/redact")
async def redact_pdf(file: UploadFile = File(...)):
    """Redacts sensitive information from an uploaded PDF and returns the redacted file."""
    # Read the uploaded file into memory
    file_content = await file.read()

    # Create a BytesIO stream for the uploaded file
    input_pdf = io.BytesIO(file_content)

    # Perform redaction on the PDF
    redacted_pdf = redact_submission_ids(input_pdf)

    # Return the redacted PDF directly as a streaming response
    return StreamingResponse(redacted_pdf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={file.filename}"})
