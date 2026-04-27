import pytest
from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image

client = TestClient(app)

def create_test_image(width, height, format="JPEG", mode="RGB"):
    file = io.BytesIO()
    image = Image.new(mode, (width, height), color='red')
    image.save(file, format=format)
    file.seek(0)
    return file.read()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    image_bytes = create_test_image(2000, 1000)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Check if resized correctly
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    # Original ratio 2:1 -> 1600:800
    assert output_img.height == 800

def test_compress_small_image():
    # Should not upscale
    image_bytes = create_test_image(100, 100)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 100
    assert output_img.height == 100

def test_compress_rgba():
    image_bytes = create_test_image(100, 100, format="PNG", mode="RGBA")
    response = client.post(
        "/compress",
        files={"file": ("test.png", image_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.mode == "RGB"

def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_compress_file_too_large(monkeypatch):
    # Lower the MAX_FILE_SIZE for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    image_bytes = create_test_image(100, 100)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
