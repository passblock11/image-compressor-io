import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    # Create large 2000x1000 JPEG
    img = Image.new("RGB", (2000, 1000), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800


def test_compress_small_image():
    # Create small 800x600 image
    img = Image.new("RGB", (800, 600), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf, "image/jpeg")},
    )

    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    # Should maintain original size if width <= 1600
    assert out_img.size == (800, 600)


def test_compress_rgba_png():
    # Create RGBA PNG image
    img = Image.new("RGBA", (1800, 1200), color=(0, 0, 255, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"0123456789abcde", "image/jpeg")},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}
