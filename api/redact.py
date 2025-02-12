import io
import fitz  # PyMuPDF
from flask import Flask, send_file, request

app = Flask(__name__)

@app.route('/redact', methods=['POST'])
def redact_submission_ids():
    """Redacts Submission IDs and places a white rectangle above 'Document Details' on the first page."""
    input_pdf = request.files['file']  # PDF file uploaded via the form
    filename = input_pdf.filename  # Extract the original filename

    doc = fitz.open(input_pdf)

    # Redact Submission IDs
    for page_num, page in enumerate(doc):
        text_instances = page.search_for("Submission ID trn:oid:::")
        for inst in text_instances:
            rect = fitz.Rect(inst.x0, inst.y0, inst.x1 + 100, inst.y1)  # Expand width as needed
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # White rectangle

        # If it's the first page, place a white rectangle above "Document Details"
        if page_num == 0:
            details_instances = page.search_for("Document Details")
            for inst in details_instances:
                # Draw above "Document Details" with increased width
                rect = fitz.Rect(0, inst.y0 - 50, page.rect.x1, inst.y0)  # Extend width fully
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # White rectangle

    # Save the redacted PDF to an in-memory byte stream
    output_pdf = io.BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)

    # Return the PDF as a downloadable file with the same name as the original
    return send_file(output_pdf, as_attachment=True, download_name=filename, mimetype='application/pdf')
