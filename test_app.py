import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import app as app_module
from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_png():
    # Generate a small RGBA PNG image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify response is a valid JPEG and size is correct
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (100, 100)


def test_compress_large_jpeg():
    # Generate a large JPEG image (> 1600 width)
    img = Image.new("RGB", (2000, 1000), color=(0, 255, 0))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify response is resized to 1600 width, preserving aspect ratio (height should be 800)
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (1600, 800)


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.txt", b"", "text/plain")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("bad.png", b"not-an-image-file", "image/png")}
    )
    assert response.status_code == 400
    assert "Invalid image" in response.json()["detail"]


def test_compress_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 5)
    response = client.post(
        "/compress",
        files={"file": ("large.png", b"more-than-five-bytes", "image/png")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
