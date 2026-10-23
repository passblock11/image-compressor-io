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


def test_compress_small_jpeg():
    im = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_im = Image.open(io.BytesIO(response.content))
    assert out_im.size == (800, 600)
    assert out_im.format == "JPEG"


def test_compress_large_jpeg():
    im = Image.new("RGB", (3000, 2000), color="red")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_im = Image.open(io.BytesIO(response.content))
    assert out_im.width == 1600
    assert abs(out_im.height - 1067) <= 1
    assert out_im.format == "JPEG"


def test_compress_rgba_png():
    im = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    im.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_im = Image.open(io.BytesIO(response.content))
    assert out_im.width == 1600
    assert abs(out_im.height - 800) <= 1
    assert out_im.mode == "RGB"


def test_compress_la_png():
    im = Image.new("LA", (2000, 1000), color=(128, 200))
    buf = io.BytesIO()
    im.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_im = Image.open(io.BytesIO(response.content))
    assert out_im.width == 1600
    assert abs(out_im.height - 800) <= 1
    assert out_im.mode == "RGB"


def test_compress_cmyk_jpeg():
    im = Image.new("CMYK", (2000, 1000), color=(100, 50, 0, 0))
    buf = io.BytesIO()
    im.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_im = Image.open(io.BytesIO(response.content))
    assert out_im.width == 1600
    assert abs(out_im.height - 800) <= 1
    assert out_im.mode == "RGB"


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
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"x" * 101, "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
