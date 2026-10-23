# I-Hate-Pdf

An independent open-source PDF workspace by [Rolex_key](https://github.com/sajinstalin01). It uses its own name and visual identity and is inspired by common online PDF utility workflows. It is not affiliated with iLovePDF and does not copy proprietary source code or artwork.

## Features

### Browser-only tools
- Responsive tool dashboard, search and category filters
- Light/dark theme and mobile navigation
- Drag-and-drop and file picker
- Merge PDFs
- Extract one page
- Delete selected pages
- Extract multiple selected pages
- Reorder pages by entering a sequence
- Crop page boxes
- Rotate pages
- Add text watermarks and page numbers
- Convert JPG/JPEG/PNG/WebP images to PDF
- Render PDF pages as JPGs and download a ZIP
- Re-save PDF structure (this is not guaranteed to reduce file size)

### Optional backend API
The Flask API in `server.py` adds merge, page extraction/deletion/reordering, rotation, crop, watermark, numbering, Ghostscript compression, password protection, password-based unlock for authorized documents, PDF text extraction, OCR, PDF-to-DOCX, Office-to-PDF, HTML-to-PDF, exact-text redaction, image-signature placement, repair-by-rewrite, and text-based PDF comparison. Some operations require external system tools.

The backend is optional and is not automatically deployed to GitHub Pages. The Dockerfile includes LibreOffice, Ghostscript and Tesseract packages for a self-hosted deployment. See [API.md](API.md).

## Run the static website

```bash
git clone https://github.com/sajinstalin01/I-Hate-Pdf.git
cd I-Hate-Pdf
python -m http.server 8000
```

Open http://localhost:8000. PDF libraries are loaded from public CDNs, so internet access is needed unless you vendor those dependencies locally.

## Run the full-stack app locally

Python 3.12 is recommended. Install the optional system dependencies (LibreOffice, Ghostscript and Tesseract) if you need their conversion/OCR features.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Open http://127.0.0.1:5000. The Flask server serves the website and API from the same origin. For a GitHub Pages frontend and separately hosted API, edit `config.js` and set `window.IHP_API_BASE` to the API's HTTPS origin; set the backend `ALLOWED_ORIGINS` to include the exact frontend origin.

## Docker

```bash
docker build -t i-hate-pdf .
docker run --rm -p 5000:5000 -e MAX_UPLOAD_MB=40 i-hate-pdf
```

Visit http://localhost:5000. Do not expose a public processing service without a deployment review, rate limiting, authentication or abuse controls, resource limits, and a privacy policy.

## Tests

```bash
pip install pytest Flask Werkzeug pypdf reportlab
pytest -q
```

The current smoke tests check health, tool catalogue and missing-upload validation. Add sample-file regression tests before production use.

## Backend operations and limits

- Uploads are limited by `MAX_UPLOAD_MB` (default 40 MB) and `MAX_FILES` (default 20).
- Backend responses are downloads; the app does not maintain a document history or cloud library.
- OCR needs Tesseract language data; PDF-to-DOCX needs pdf2docx; Office conversion needs LibreOffice; compression needs Ghostscript; HTML-to-PDF needs WeasyPrint system libraries.
- PDF/A conversion is intentionally not enabled until an administrator configures and validates an ICC profile and Ghostscript policy.
- `sign-image` places a visible image and is **not** a cryptographic digital signature.
- Redaction is limited to selectable exact text matches. Carefully verify output; scanned pages and other content types may need a separate workflow.
- Text comparison is not a visual pixel-by-pixel comparison.
- Rewriting a PDF does not guarantee repair of every malformed file or a smaller output.
- User accounts, cloud storage integrations, remote history, a full visual editor, and cryptographic signature creation/verification are not implemented.

## Privacy and security

Browser-only operations process files locally. When the optional backend is configured, selected files are sent to that server for processing. Deploy only to infrastructure you trust. Configure HTTPS, origin allowlists, rate limits, request timeouts, monitoring, and operational file-cleanup policies. Never put secrets in `config.js` or commit them to Git.

## License

MIT. See [LICENSE](LICENSE).
