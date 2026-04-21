from fastapi.testclient import TestClient
from app import app, MAX_FILE_SIZE
import io
from PIL import Image
import pytest

client = TestClient(app)

def create_test_image(size=(100, 100), format='JPEG'):
    img = Image.new('RGB', size, color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=format)
    return img_byte_arr.getvalue()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_success():
    image_data = create_test_image()
    response = client.post("/compress", files={"file": ("test.jpg", image_data, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify it's a valid image
    img = Image.open(io.BytesIO(response.content))
    assert img.format == "JPEG"

def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("test.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("test.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_compress_file_too_large(monkeypatch):
    # Lower MAX_FILE_SIZE for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    image_data = create_test_image()
    response = client.post("/compress", files={"file": ("test.jpg", image_data, "image/jpeg")})
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
