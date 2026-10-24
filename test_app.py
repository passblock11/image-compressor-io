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


def test_compress_large_image():
    # Create large image (>1600 width)
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
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800


def test_compress_small_image():
    # Create small image (<=1600 width)
    img = Image.new("RGB", (800, 600), color="blue")
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
    assert out_img.size[0] == 800
    assert out_img.size[1] == 600


def test_compress_rgba_image():
    img = Image.new("RGBA", (1800, 1200), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 1600


def test_compress_empty_file():
    buf = io.BytesIO(b"")
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    buf = io.BytesIO(b"this is not an image file")
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", buf, "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
