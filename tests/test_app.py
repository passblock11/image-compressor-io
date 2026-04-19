import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import app, MAX_FILE_SIZE

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_image():
    # Create a simple red image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_compress_large_file(monkeypatch):
    # Use monkeypatch to lower the MAX_FILE_SIZE for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)

    img = Image.new('RGB', (200, 200), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Ensure the image is larger than 100 bytes
    assert len(img_byte_arr.getvalue()) > 100

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
