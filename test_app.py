import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_success(client):
    # Create 2000x1000 JPEG image (exceeds MAX_WIDTH 1600)
    img = Image.new("RGB", (2000, 1000), color=(250, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post("/compress", files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    compressed_img = Image.open(io.BytesIO(response.content))
    assert compressed_img.size == (1600, 800)
    assert compressed_img.format == "JPEG"


def test_compress_small_jpeg_no_upscale(client):
    # Create 800x600 JPEG image (under MAX_WIDTH 1600)
    img = Image.new("RGB", (800, 600), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post("/compress", files={"file": ("small.jpg", jpeg_bytes, "image/jpeg")})
    assert response.status_code == 200

    compressed_img = Image.open(io.BytesIO(response.content))
    assert compressed_img.size == (800, 600)


def test_compress_rgba_conversion(client):
    # Create RGBA image with alpha channel
    img = Image.new("RGBA", (2000, 1000), color=(100, 200, 50, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post("/compress", files={"file": ("test.png", png_bytes, "image/png")})
    assert response.status_code == 200

    compressed_img = Image.open(io.BytesIO(response.content))
    assert compressed_img.mode == "RGB"
    assert compressed_img.size == (1600, 800)


def test_compress_empty_file(client):
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image_file(client):
    response = client.post("/compress", files={"file": ("invalid.jpg", b"not an image", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(client, monkeypatch):
    # Temporarily set MAX_FILE_SIZE to 10 bytes for size testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)

    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post("/compress", files={"file": ("large.jpg", jpeg_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
