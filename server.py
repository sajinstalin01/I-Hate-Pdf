"""I-Hate-Pdf optional processing API.

Run with: pip install -r requirements.txt && python server.py
Use only on trusted deployments. Temporary uploads are handled in-memory or in
request-scoped temporary directories and are not retained as a document library.
"""
from __future__ import annotations
import difflib, io, os, shutil, subprocess, tempfile
from pathlib import Path
from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "40")) * 1024 * 1024
ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".html", ".htm", ".txt"}
MAX_FILES = int(os.getenv("MAX_FILES", "20"))

def err(message, code=400):
    return jsonify({"error": message}), code

def parse_pages(value, count):
    if not value:
        return list(range(count))
    out = []
    for part in value.split(","):
        part = part.strip()
        if not part: continue
        if "-" in part:
            a, b = part.split("-", 1); start, end = int(a), int(b)
            if start < 1 or end < start or end > count: raise ValueError(f"Page range {part} is outside 1-{count}")
            out.extend(range(start - 1, end))
        else:
            n = int(part)
            if n < 1 or n > count: raise ValueError(f"Page {n} is outside 1-{count}")
            out.append(n - 1)
    return list(dict.fromkeys(out))

def uploaded_files():
    files = request.files.getlist("files") or ([request.files["file"]] if "file" in request.files else [])
    if not files: raise ValueError("Upload at least one file using 'files' or 'file'.")
    if len(files) > MAX_FILES: raise ValueError(f"Maximum {MAX_FILES} files per request.")
    items = []
    for f in files:
        name = secure_filename(f.filename or "")
        if not name: raise ValueError("Every uploaded file must have a filename.")
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED: raise ValueError(f"Unsupported file type: {ext or '(no extension)'}")
        items.append((name, f.read()))
    return items

def pdf_reader(data, password=""):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted and (not password or not reader.decrypt(password)):
        raise ValueError("PDF is encrypted. Provide the correct password if you are authorized to access it.")
    return reader

def pdf_bytes(writer):
    stream = io.BytesIO(); writer.write(stream); return stream.getvalue()

def pdf_response(data, filename="output.pdf", mimetype="application/pdf"):
    return send_file(io.BytesIO(data), mimetype=mimetype, as_attachment=True, download_name=filename)

def tool_error(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try: return fn(*args, **kwargs)
        except ValueError as e: return err(str(e), 400)
        except ImportError as e: return err(f"Optional dependency missing: {e.name}. Install requirements.txt.", 501)
        except Exception as e:
            app.logger.exception("PDF operation failed")
            return err(f"Could not process this document: {e}", 422)
    return wrapper

@app.get("/")
def home():
    return send_from_directory(Path(__file__).resolve().parent, "index.html")

@app.get("/styles.css")
def styles():
    return send_from_directory(Path(__file__).resolve().parent, "styles.css")

@app.get("/app.js")
def frontend_js():
    return send_from_directory(Path(__file__).resolve().parent, "app.js")

@app.get("/api/health")
def health():
    return jsonify({"name":"I-Hate-Pdf API","status":"ok","max_upload_mb":app.config["MAX_CONTENT_LENGTH"]//(1024*1024)})

@app.get("/api/tools")
def tool_catalogue():
    return jsonify({"operations":["merge","split","extract-pages","delete-pages","reorder-pages","rotate","watermark","page-numbers","crop","compress","protect","unlock","repair","pdf-to-text","ocr","pdf-to-docx","office-to-pdf","jpg-to-pdf","html-to-pdf","redact","sign-image","compare"],
      "note":"Optional operations require system dependencies. PDF/A conversion and cryptographic signing are not implemented. See API.md."})

@app.post("/api/process/<operation>")
@tool_error
def process(operation):
    items = uploaded_files(); form = request.form
    outname = secure_filename(form.get("output_name", "output")) or "output"
    if not outname.lower().endswith(".pdf"): outname += ".pdf"
    if operation == "merge":
        from pypdf import PdfWriter
        writer = PdfWriter()
        for name, data in items:
            if not name.lower().endswith(".pdf"): raise ValueError("Merge accepts PDF files only.")
            writer.append(pdf_reader(data, form.get("password", "")))
        return pdf_response(pdf_bytes(writer), outname)

    if operation in {"split","extract-pages","delete-pages","reorder-pages","rotate","watermark","page-numbers","crop","protect","unlock","repair","pdf-to-text","ocr","pdf-to-docx","compress","pdfa","redact","sign-image"}:
        name, data = items[0]; password = form.get("password", "")
        reader = pdf_reader(data, password)
        from pypdf import PdfReader, PdfWriter
        if operation in {"split","extract-pages","delete-pages","reorder-pages","rotate","watermark","page-numbers","crop","protect","unlock","repair"}:
            writer = PdfWriter(); count = len(reader.pages)
            if operation in {"split","extract-pages"}:
                selected = parse_pages(form.get("pages", "1" if operation == "split" else ""), count)
                for i in selected: writer.add_page(reader.pages[i])
            elif operation == "delete-pages":
                removed = set(parse_pages(form.get("pages", ""), count))
                if len(removed) == count: raise ValueError("Cannot delete every page.")
                for i, page in enumerate(reader.pages):
                    if i not in removed: writer.add_page(page)
            elif operation == "reorder-pages":
                selected = parse_pages(form.get("pages", ""), count)
                if len(selected) != count or set(selected) != set(range(count)):
                    raise ValueError("List every page exactly once, e.g. 3,1,2.")
                for i in selected: writer.add_page(reader.pages[i])
            elif operation == "rotate":
                degrees = int(form.get("degrees", "90")) % 360
                if degrees not in {0,90,180,270}: raise ValueError("Rotation must be 0, 90, 180, or 270.")
                for page in reader.pages: page.rotate(degrees); writer.add_page(page)
            elif operation == "watermark":
                from reportlab.pdfgen import canvas
                text = form.get("text", "").strip()
                if not text: raise ValueError("Watermark text is required.")
                for page in reader.pages:
                    w,h=float(page.mediabox.width),float(page.mediabox.height)
                    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(w,h)); c.saveState(); c.setFillAlpha(.25); c.setFillColorRGB(.85,.15,.12); c.setFont("Helvetica-Bold",28); c.translate(w/2,h/2); c.rotate(35); c.drawCentredString(0,0,text[:180]); c.restoreState(); c.save()
                    page.merge_page(PdfReader(io.BytesIO(buf.getvalue())).pages[0]); writer.add_page(page)
            elif operation == "page-numbers":
                from reportlab.pdfgen import canvas
                start=int(form.get("start","1"))
                if start < 0: raise ValueError("Starting number cannot be negative.")
                for i,page in enumerate(reader.pages):
                    w,h=float(page.mediabox.width),float(page.mediabox.height)
                    buf=io.BytesIO(); c=canvas.Canvas(buf,pagesize=(w,h)); c.setFont("Helvetica",10); c.drawCentredString(w/2,18,str(start+i)); c.save()
                    page.merge_page(PdfReader(io.BytesIO(buf.getvalue())).pages[0]); writer.add_page(page)
            elif operation == "crop":
                x=float(form.get("x","0")); y=float(form.get("y","0")); w=float(form.get("width","0")); h=float(form.get("height","0"))
                if min(x,y,w,h)<0 or w<=0 or h<=0: raise ValueError("Crop requires non-negative x/y and positive width/height.")
                for page in reader.pages:
                    if x+w>float(page.mediabox.width) or y+h>float(page.mediabox.height): raise ValueError("Crop rectangle exceeds page boundary.")
                    page.mediabox.lower_left=(x,y); page.mediabox.upper_right=(x+w,y+h); writer.add_page(page)
            elif operation == "protect":
                pw=form.get("new_password","")
                if len(pw)<8: raise ValueError("Choose a password of at least 8 characters.")
                for page in reader.pages: writer.add_page(page)
                writer.encrypt(pw, algorithm="AES-256")
            elif operation in {"unlock","repair"}:
                for page in reader.pages: writer.add_page(page)
            return pdf_response(pdf_bytes(writer), outname)

        if operation == "pdf-to-text":
            return pdf_response(("\n\n".join(p.extract_text() or "" for p in reader.pages)).encode(), Path(name).stem+".txt", "text/plain; charset=utf-8")
        if operation == "ocr":
            import fitz, pytesseract
            from PIL import Image
            doc=fitz.open(stream=data,filetype="pdf"); pages=[]
            limit=min(len(doc),max(1,int(form.get("max_pages","30"))))
            for page in doc[:limit]:
                pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
                pages.append(pytesseract.image_to_string(Image.open(io.BytesIO(pix.tobytes("png"))),lang=form.get("lang","eng")))
            return pdf_response(("\n\n".join(pages)).encode(), Path(name).stem+"-ocr.txt", "text/plain; charset=utf-8")
        if operation == "pdf-to-docx":
            from pdf2docx import Converter
            with tempfile.TemporaryDirectory(prefix="ihp-") as td:
                src=Path(td)/"source.pdf"; dst=Path(td)/"output.docx"; src.write_bytes(data)
                cv=Converter(str(src)); cv.convert(str(dst)); cv.close()
                return send_file(io.BytesIO(dst.read_bytes()),as_attachment=True,download_name=Path(name).stem+".docx",mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if operation == "compress":
            gs=shutil.which("gs") or shutil.which("gswin64c")
            if not gs: return err("Compression requires Ghostscript on the server.",501)
            quality=form.get("quality","ebook")
            if quality not in {"screen","ebook","printer","prepress"}: raise ValueError("Invalid compression quality.")
            with tempfile.TemporaryDirectory(prefix="ihp-") as td:
                src=Path(td)/"in.pdf"; dst=Path(td)/"out.pdf"; src.write_bytes(data)
                p=subprocess.run([gs,"-sDEVICE=pdfwrite","-dCompatibilityLevel=1.5","-dNOPAUSE","-dBATCH","-dQUIET",f"-dPDFSETTINGS=/{quality}",f"-sOutputFile={dst}",str(src)],capture_output=True,timeout=120)
                if p.returncode or not dst.exists(): raise ValueError("Ghostscript compression failed.")
                return pdf_response(dst.read_bytes(),outname)
        if operation == "pdfa":
            return err("PDF/A conversion is not enabled: an administrator must configure and validate an ICC profile and Ghostscript PDF/A policy.",501)
        if operation == "redact":
            import fitz
            terms=[t.strip() for t in form.get("terms","").splitlines() if t.strip()]
            if not terms: raise ValueError("Provide exact text terms, one per line.")
            doc=fitz.open(stream=data,filetype="pdf"); matches=0
            for page in doc:
                for term in terms:
                    for rect in page.search_for(term):
                        page.add_redact_annot(rect,fill=(0,0,0)); matches+=1
                page.apply_redactions()
            if not matches: raise ValueError("No matching selectable text was found.")
            return pdf_response(doc.tobytes(garbage=4,deflate=True),outname)
        if operation == "sign-image":
            import fitz
            sig=request.files.get("signature")
            if not sig: raise ValueError("Upload a signature image using field 'signature'.")
            rect=[float(v) for v in form.get("rect","50,50,250,110").split(",")]
            if len(rect)!=4 or rect[2]<=rect[0] or rect[3]<=rect[1]: raise ValueError("Signature rect must be x0,y0,x1,y1.")
            doc=fitz.open(stream=data,filetype="pdf"); page_num=int(form.get("page","1"))
            if page_num<1 or page_num>len(doc): raise ValueError("Signature page is out of range.")
            doc[page_num-1].insert_image(fitz.Rect(*rect),stream=sig.read(),keep_proportion=True)
            return pdf_response(doc.tobytes(),outname)
    if operation == "jpg-to-pdf":
        from PIL import Image
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        buf=io.BytesIO(); c=canvas.Canvas(buf)
        for name,data in items:
            im=Image.open(io.BytesIO(data)).convert("RGB"); w,h=im.size; scale=min(595/w,842/h,1)
            c.setPageSize((w*scale+36,h*scale+36)); c.drawImage(ImageReader(im),18,18,width=w*scale,height=h*scale); c.showPage()
        c.save(); return pdf_response(buf.getvalue(),outname)
    if operation == "office-to-pdf":
        office=shutil.which("libreoffice") or shutil.which("soffice")
        if not office: return err("Office conversion requires LibreOffice on the server.",501)
        with tempfile.TemporaryDirectory(prefix="ihp-") as td:
            srcdir=Path(td)/"in"; outdir=Path(td)/"out"; srcdir.mkdir(); outdir.mkdir()
            for name,data in items: (srcdir/secure_filename(name)).write_bytes(data)
            for f in srcdir.iterdir():
                p=subprocess.run([office,"--headless","--convert-to","pdf","--outdir",str(outdir),str(f)],capture_output=True,timeout=120)
                if p.returncode: raise ValueError(f"Conversion failed for {f.name}: {p.stderr.decode(errors='ignore')[:200]}")
            pdfs=list(outdir.glob("*.pdf"))
            if not pdfs: raise ValueError("No PDF output generated.")
            return pdf_response(pdfs[0].read_bytes(),outname)
    if operation == "html-to-pdf":
        try: from weasyprint import HTML
        except ImportError: return err("HTML conversion requires WeasyPrint and system libraries.",501)
        return pdf_response(HTML(string=items[0][1].decode("utf-8","replace")).write_pdf(),outname)
    if operation == "compare":
        if len(items)<2: raise ValueError("Upload two PDF files to compare.")
        texts=[]
        for _,data in items[:2]: texts.append("\n".join(p.extract_text() or "" for p in pdf_reader(data,form.get("password","")).pages).splitlines())
        diff="\n".join(difflib.unified_diff(texts[0],texts[1],fromfile=items[0][0],tofile=items[1][0],lineterm=""))
        return pdf_response(diff.encode(),"pdf-comparison.txt","text/plain; charset=utf-8")
    return err(f"Unknown operation: {operation}",404)

@app.errorhandler(413)
def too_large(_):
    return err(f"Upload too large. Limit is {app.config['MAX_CONTENT_LENGTH']//(1024*1024)} MB.",413)

@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options","nosniff")
    response.headers.setdefault("X-Frame-Options","DENY")
    response.headers.setdefault("Referrer-Policy","no-referrer")
    response.headers.setdefault("Cache-Control","no-store")
    origin = request.headers.get("Origin")
    allowed = {v.strip() for v in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",") if v.strip()}
    if origin and origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Vary"] = "Origin"
    return response

if __name__ == "__main__":
    app.run(host=os.getenv("HOST","127.0.0.1"),port=int(os.getenv("PORT","5000")),debug=False)
