from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image
import pytest

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    # Create a small valid JPEG
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify it's a valid image
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"

def test_compress_large_image_resizing():
    # Create an image larger than MAX_WIDTH (1600)
    img = Image.new('RGB', (2000, 1000), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    # Aspect ratio should be preserved: 1000 * (1600/2000) = 800
    assert out_img.height == 800

def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_file_too_large(monkeypatch):
    # Mock MAX_FILE_SIZE to a small value for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)

    img_byte_arr = b"a" * 101
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
