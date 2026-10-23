# I-Hate-Pdf Processing API

Optional Flask backend for advanced document operations. This is separate from the static front end.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python server.py
```
The API listens on `http://127.0.0.1:5000`. Check `GET /api/health` and `GET /api/tools`.

## Request format
Use `multipart/form-data`. Upload a single file as `file`, or several as repeated `files` fields. Successful responses are downloads; errors return JSON.

```bash
curl -f -X POST http://127.0.0.1:5000/api/process/rotate -F 'file=@input.pdf' -F 'degrees=90' -o rotated.pdf
curl -f -X POST http://127.0.0.1:5000/api/process/merge -F 'files=@one.pdf' -F 'files=@two.pdf' -o merged.pdf
```

## Operations
| Operation | Fields | Notes |
|---|---|---|
| merge | files | Merge PDFs in upload order |
| split / extract-pages | file, pages=1,3-5 | Extract selected pages |
| delete-pages | file, pages=2,4 | Remove selected pages |
| reorder-pages | file, pages=3,1,2 | List every page exactly once |
| rotate | file, degrees=90 | 0, 90, 180, 270 |
| watermark | file, text | Diagonal text stamp |
| page-numbers | file, start=1 | Bottom-centre numbering |
| crop | file, x, y, width, height | Points, same rectangle on each page |
| compress | file, quality=screen/ebook/printer/prepress | Requires Ghostscript |
| protect | file, new_password | AES-256 encryption via pypdf |
| unlock | file, password | Requires the correct password and authorization |
| repair | file | Rewrites many malformed PDFs; not guaranteed |
| pdf-to-text | file | Extract selectable text |
| ocr | file, lang=eng, max_pages=30 | Requires Tesseract, language data and PyMuPDF |
| pdf-to-docx | file | Requires pdf2docx; complex layouts may change |
| office-to-pdf | files | Requires LibreOffice; returns first converted file |
| jpg-to-pdf | files | JPG/PNG/WebP images |
| html-to-pdf | file containing HTML | Requires WeasyPrint system libraries |
| redact | file, terms | Exact selectable text, one term per line; verify output carefully |
| sign-image | file, signature image, page, rect | Places visible signature art; **not** a cryptographic digital signature |
| compare | two files | Text-based unified diff, not visual comparison |

## Limitations
- This API is not automatically connected to the static browser UI.
- PDF/A conversion requires administrator-configured ICC profiles and validation; it is not enabled.
- Cryptographic digital signatures, user accounts, cloud drives, remote history, and a full visual editor are not implemented.
- OCR requires system Tesseract binaries and requested language packs.
- A PDF rewrite or compression may not reduce file size.
