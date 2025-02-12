from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import fitz  # PyMuPDF
import os
import shutil

app = FastAPI()

# Vercel environment uses /tmp directory for temporary file storage
UPLOAD_DIR = "/tmp"
STATIC_DIR = "/static"  # Make sure this is publicly accessible
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

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

@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    """Serves an HTML form to upload a PDF file."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Redaction</title>
    </head>
    <body>
        <h2>Upload PDF to Redact</h2>
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" id="fileInput" name="file" accept=".pdf" required />
            <button type="submit">Upload and Redact</button>
        </form>
        <div id="status"></div>
        <script>
            const form = document.getElementById('uploadForm');
            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const formData = new FormData();
                formData.append('file', document.getElementById('fileInput').files[0]);

                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = 'Processing...';

                const response = await fetch('/api/redact', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (data.redacted_pdf) {
                    statusDiv.innerHTML = 'Redaction complete! Downloading your file...';
                    window.location.href = data.redacted_pdf;
                } else {
                    statusDiv.innerHTML = 'Error during redaction';
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/redact")
async def redact_pdf(file: UploadFile = File(...)):
    """Redacts sensitive information from an uploaded PDF."""
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    output_path = os.path.join(STATIC_DIR, f"redacted_{file.filename}")

    # Save the uploaded PDF to /tmp
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Perform redaction and save the result to the /static directory
    redact_submission_ids(input_path, output_path)

    # Return the redacted PDF download URL (accessible via /static)
    return {"message": "Redaction complete", "redacted_pdf": f"/static/redacted_{file.filename}"}

@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """Allows downloading of the redacted PDF."""
    file_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    return {"error": "File not found"}
