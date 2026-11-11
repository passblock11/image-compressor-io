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


def test_compress_jpeg_resize():
    # Create image with width > 1600
    im = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_small_image():
    # Create image with width <= 1600 (no resize needed)
    im = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)
    assert out_img.format == "JPEG"


def test_compress_rgba_conversion():
    # RGBA image should be converted to RGB without errors
    im = Image.new("RGBA", (1000, 500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("rgba.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.format == "JPEG"


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("invalid.jpg", b"not-a-valid-image", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 50)
    im = Image.new("RGB", (200, 200), color="red")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
