


#!/usr/bin/env python3

import os
import tempfile
import magic
from docx import Document
from mcp.server.lowlevel.server import Server, RequestResponder
from typing import Optional, List

class DocToMarkdownServer:
    def __init__(self):
        self.server = Server(
            name="DOC to Markdown Converter",
            version="1.0.0",
            instructions="Converts DOC and DOCX files to Markdown format"
        )

        # Register the file processor
        self.server.register_file_processor(self.process_file)

    def is_valid_doc_file(self, mime_type: str) -> bool:
        """Check if file is a valid DOC or DOCX file"""
        return mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

    def docx_to_markdown(self, file_path: str) -> str:
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

    async def process_file(self, request_ctx: RequestResponder) -> None:
        """Process a file stream and convert it to markdown"""
        try:
            # Get the uploaded file
            file_stream = await request_ctx.get_file()

            if not file_stream or not file_stream.metadata.name:
                await request_ctx.send_error("No file provided")
                return

            # Get temporary file path
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_stream.metadata.name)[1]) as tmp_file:
                temp_path = tmp_file.name

            # Write chunks to temporary file
            async for chunk in file_stream.chunks:
                if chunk.data:
                    with open(temp_path, 'ab') as f:
                        f.write(chunk.data)

            # Determine MIME type
            mime_type = magic.from_file(temp_path, mime=True)

            if not self.is_valid_doc_file(mime_type):
                await request_ctx.send_error(
                    f"Unsupported file type: {mime_type}. Please provide a .doc or .docx file."
                )
                os.unlink(temp_path)
                return

            # Process the file based on its type
            markdown_content = ""
            if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                markdown_content = self.docx_to_markdown(temp_path)
            elif mime_type == 'application/msword':
                markdown_content = f"DOC files are not directly supported. Please convert to DOCX format."

            # Clean up temporary file
            os.unlink(temp_path)

            await request_ctx.send_success(
                content=markdown_content,
                metadata={
                    "format": "markdown",
                    "original_format": mime_type.split('/')[-1].upper()
                }
            )

        except Exception as e:
            await request_ctx.send_error(f"Error processing file: {str(e)}")

    def run(self, host: str = "0.0.0.0", port: int = 5000):
        """Run the MCP server"""
        import uvicorn
        from mcp.server.lowlevel.stdio_server import create_app

        app = create_app(self.server)

        print(f"Starting server on http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    server = DocToMarkdownServer()
    server.run(host="0.0.0.0", port=5000)


