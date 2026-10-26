import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg(client):
    # Create a 2000x1000 RGB image
    img = Image.new("RGB", (2000, 1000), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    # Should be resized to width 1600, preserving aspect ratio (height 800)
    assert out_img.size == (1600, 800)


def test_compress_rgba_image(client):
    # Create an RGBA image smaller than MAX_WIDTH (1000x500)
    img = Image.new("RGBA", (1000, 500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")}
    )

    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"
    assert out_img.size == (1000, 500)


def test_compress_palette_image(client):
    # Create a Palette (P) mode image
    img = Image.new("P", (800, 600), color=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("palette.png", buf, "image/png")}
    )

    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"


def test_compress_empty_file(client):
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image_file(client):
    response = client.post(
        "/compress",
        files={"file": ("notimage.txt", io.BytesIO(b"this is not an image file"), "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(client, monkeypatch):
    # Temporarily set MAX_FILE_SIZE to 10 bytes for test
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", io.BytesIO(b"123456789012345"), "image/jpeg")}
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
