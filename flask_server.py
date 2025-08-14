



#!/usr/bin/env python3

import os
import tempfile
import magic
from flask import Flask, request, jsonify
from docx import Document
from werkzeug.utils import secure_filename

app = Flask(__name__)

def is_valid_doc_file(mime_type: str) -> bool:
    """Check if file is a valid DOC or DOCX file"""
    return mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

def docx_to_markdown(file_path: str) -> str:
    """Convert DOCX file to markdown"""
    try:
        doc = Document(file_path)
        text_lines = []
        for para in doc.paragraphs:
            if para.text.strip():
                # Convert paragraphs to markdown format
                text_lines.append(para.text)

        return "\n\n".join(text_lines)
    except Exception as e:
        return f"Error converting DOCX to Markdown: {str(e)}"

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and convert to markdown"""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    # Get temporary file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        temp_path = tmp_file.name

    try:
        file.save(temp_path)

        # Determine MIME type
        mime_type = magic.from_file(temp_path, mime=True)

        if not is_valid_doc_file(mime_type):
            return jsonify({
                "status": "error",
                "message": f"Unsupported file type: {mime_type}. Please provide a .doc or .docx file."
            }), 400

        # Process the file based on its type
        markdown_content = ""
        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            markdown_content = docx_to_markdown(temp_path)
        elif mime_type == 'application/msword':
            markdown_content = f"DOC files are not directly supported. Please convert to DOCX format."

        return jsonify({
            "status": "success",
            "content": markdown_content,
            "metadata": {
                "format": "markdown",
                "original_format": mime_type.split('/')[-1].upper()
            }
        })

    except Exception as e:
        os.unlink(temp_path)
        return jsonify({"status": "error", "message": f"Error processing file: {str(e)}"}), 500

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



