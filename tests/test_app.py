
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import app, MAX_FILE_SIZE

client = TestClient(app)

def create_test_image(size=(100, 100), format='JPEG', mode='RGB'):
    file = io.BytesIO()
    image = Image.new(mode, size, color='red')
    image.save(file, format)
    file.seek(0)
    return file

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_success():
    img_file = create_test_image()
    response = client.post("/compress", files={"file": ("test.jpg", img_file, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify it's a valid JPEG
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"

def test_compress_resize():
    # Width 2000 > 1600
    img_file = create_test_image(size=(2000, 1000))
    response = client.post("/compress", files={"file": ("test.jpg", img_file, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    # 1000 * (1600 / 2000) = 800
    assert out_img.size[1] == 800

def test_compress_no_resize():
    # Width 800 <= 1600
    img_file = create_test_image(size=(800, 600))
    response = client.post("/compress", files={"file": ("test.jpg", img_file, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)

def test_compress_rgba_to_rgb():
    img_file = create_test_image(mode='RGBA', format='PNG')
    response = client.post("/compress", files={"file": ("test.png", img_file, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.format == "JPEG"

def test_empty_file():
    response = client.post("/compress", files={"file": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_invalid_image():
    response = client.post("/compress", files={"file": ("not_image.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_file_too_large(monkeypatch):
    # Mock MAX_FILE_SIZE to something small for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    img_file = create_test_image(size=(100, 100)) # This will definitely be > 100 bytes

    response = client.post("/compress", files={"file": ("large.jpg", img_file, "image/jpeg")})
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
