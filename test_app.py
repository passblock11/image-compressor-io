import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    # Create an image wider than 1600px
    img = Image.new("RGB", (3000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify compressed image dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1066


def test_compress_small_image():
    # Image within max width limit
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_png():
    # Image with RGBA transparency
    img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.width == 1600


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"not a real image payload", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Temporarily set MAX_FILE_SIZE to 10 bytes for testing limit
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    img = Image.new("RGB", (100, 100), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
