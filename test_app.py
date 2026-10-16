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


def test_compress_valid_jpeg():
    img = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_resize_large_image():
    img = Image.new("RGB", (3000, 2000), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] in (1066, 1067)


def test_compress_rgba_png():
    img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf.getvalue(), "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1000, 1000)


def test_compress_pillow_fallback(monkeypatch):
    monkeypatch.setattr(app_module, "HAS_PYVIPS", False)
    img = Image.new("RGB", (3000, 2000), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("fallback.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_oversized_file(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    response = client.post(
        "/compress",
        files={"file": ("huge.jpg", b"0123456789abcde", "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
