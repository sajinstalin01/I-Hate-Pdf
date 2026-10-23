from server import app

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
