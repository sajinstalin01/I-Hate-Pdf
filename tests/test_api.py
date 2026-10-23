import io
from pypdf import PdfReader, PdfWriter
from server import app

def make_pdf(pages=3):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=300, height=400)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()

def test_health():
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"

def test_tool_catalogue():
    response = app.test_client().get("/api/tools")
    assert response.status_code == 200
    assert "merge" in response.json["operations"]
    assert "ocr" in response.json["operations"]

def test_rejects_missing_upload():
    response = app.test_client().post("/api/process/merge")
    assert response.status_code == 400
    assert "error" in response.json

def test_delete_pages_endpoint():
    client = app.test_client()
    response = client.post("/api/process/delete-pages", data={
        "file": (io.BytesIO(make_pdf(3)), "sample.pdf"),
        "pages": "2",
    }, content_type="multipart/form-data")
    assert response.status_code == 200
    assert len(PdfReader(io.BytesIO(response.data)).pages) == 2

def test_reorder_pages_requires_all_pages():
    client = app.test_client()
    response = client.post("/api/process/reorder-pages", data={
        "file": (io.BytesIO(make_pdf(3)), "sample.pdf"),
        "pages": "2,1",
    }, content_type="multipart/form-data")
    assert response.status_code == 400
