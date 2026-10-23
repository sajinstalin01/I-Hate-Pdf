# I-Hate-Pdf

An open-source, browser-first PDF workspace by [Rolex_key](https://github.com/sajinstalin01). This project takes inspiration from the usability patterns of online PDF tool suites, while using its own name, visual identity, and implementation.

> This is an independent project and is not affiliated with or endorsed by iLovePDF. It does not copy their proprietary source code, logos, or artwork.

## Features in this starter

- Responsive landing page and PDF-tool dashboard
- Searchable tool catalogue with category filters
- Light/dark theme toggle
- Drag-and-drop and file picker
- Local browser processing with [pdf-lib](https://github.com/Hopding/pdf-lib)
- **Implemented:** Merge PDF, extract one page (Split PDF), rotate pages, text watermark, image-to-PDF, PDF-to-JPG ZIP export, add page numbers, re-save/normalize PDF structure
- Download output directly from the browser
- Mobile-friendly layout, status messages, and error handling
- No project backend and no document uploads by this app

## Run locally

No build step is needed.

1. Clone the repository:
   ```bash
   git clone https://github.com/sajinstalin01/I-Hate-Pdf.git
   cd I-Hate-Pdf
   ```
2. Open `index.html` in a modern browser, or run a local static server:
   ```bash
   python -m http.server 8000
   ```
3. Visit http://localhost:8000.

The PDF library is loaded from jsDelivr, so an internet connection is needed for the initial page load. For offline deployment, vendor a reviewed copy of pdf-lib and update the script reference.

## Test checklist

- Open the homepage at desktop and mobile widths.
- Search for a tool and switch category tabs.
- Try merge with two small PDFs.
- Extract page 1 from a multi-page PDF.
- Rotate a PDF and verify page orientation.
- Add a watermark and page numbers.
- Convert a JPG and PNG to a PDF.
- Toggle dark mode and reload.
- Try an unsupported file type and verify the error message.
- Test large files and malformed PDFs; browser memory limits vary.

## Feature status and roadmap

The catalogue deliberately distinguishes UI placeholders from working operations. These tools are **not implemented yet**: password encryption, password removal, full page-thumbnail reordering, visual PDF editing, OCR, Office document conversion, e-signature workflows, cloud integrations, accounts, and AI features.

Suggested roadmap:
1. Add PDF.js rendering and ZIP export for PDF-to-image.
2. Add accessible thumbnail-based page selection and drag sorting.
3. Add optional backend workers for LibreOffice conversion, OCRmyPDF/Tesseract, and Ghostscript compression.
4. Add server-side queue limits, file-size limits, cleanup jobs, and secure temporary storage if a backend is introduced.
5. Add automated tests, accessibility checks, dependency pinning, and CI.

## Privacy and security

Implemented operations run in the browser; files are not uploaded by this app. The CDN dependency does make a network request to load the PDF library. Do not use this starter as a security certification or as a substitute for reviewing sensitive document workflows. Password encryption, redaction, and unlock operations need careful security design before they can be offered as production features.

## Tech stack

- HTML5, CSS3, vanilla JavaScript
- [pdf-lib 1.17.1](https://github.com/Hopding/pdf-lib) via CDN

## License

MIT — see [LICENSE](LICENSE).
