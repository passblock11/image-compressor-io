import io

from fastapi.testclient import TestClient
from PIL import Image

import app
from app import app as fastapi_app

client = TestClient(fastapi_app)


def create_image_bytes(width=2000, height=1000, fmt="JPEG", mode="RGB"):
    img = Image.new(mode, (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    img_bytes = create_image_bytes(2000, 1000, "JPEG", "RGB")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 800


def test_compress_small_jpeg():
    img_bytes = create_image_bytes(800, 600, "JPEG", "RGB")
    response = client.post(
        "/compress",
        files={"file": ("small.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 800
    assert res_img.height == 600


def test_compress_rgba_png():
    img_bytes = create_image_bytes(2000, 1000, "PNG", "RGBA")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 50)
    img_bytes = create_image_bytes(800, 600, "JPEG", "RGB")
    response = client.post(
        "/compress",
        files={"file": ("too_large.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"invalid image data", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"
