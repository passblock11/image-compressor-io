import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(size=(100, 100), mode="RGB", format="JPEG"):
    """Helper to generate in-memory test image bytes."""
    buf = io.BytesIO()
    img = Image.new(mode, size, color=(255, 0, 0) if mode != "L" else 128)
    if format == "JPEG" and mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(buf, format=format)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_image():
    img_bytes = create_test_image(size=(800, 600), mode="RGB", format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)
    assert out_img.format == "JPEG"


def test_compress_large_image_resizes():
    img_bytes = create_test_image(size=(3200, 2400), mode="RGB", format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1200)
    assert out_img.format == "JPEG"


def test_compress_rgba_mode():
    buf = io.BytesIO()
    img = Image.new("RGBA", (200, 200), color=(255, 0, 0, 128))
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("rgba.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (200, 200)


def test_compress_palette_mode():
    buf = io.BytesIO()
    img = Image.new("P", (300, 300))
    img.save(buf, format="PNG")
    p_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("palette.png", p_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (300, 300)


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
        files={"file": ("invalid.jpg", b"not-an-image-data", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 50)
    img_bytes = create_test_image(size=(100, 100), mode="RGB", format="JPEG")
    assert len(img_bytes) > 50

    response = client.post(
        "/compress",
        files={"file": ("large_file.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
