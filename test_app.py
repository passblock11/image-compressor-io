import io

from fastapi.testclient import TestClient
from PIL import Image

import app

client = TestClient(app.app)


def create_test_image(format="JPEG", size=(2000, 1000), mode="RGB", color=(255, 0, 0)):
    buf = io.BytesIO()
    img = Image.new(mode, size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    # Large image: width > 1600 (e.g. 2000x1000)
    img_bytes = create_test_image("JPEG", size=(2000, 1000))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify compressed dimensions (width should be 1600, height 800)
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_small_image():
    # Small image: width <= 1600 (e.g. 800x600) -> should not be resized
    img_bytes = create_test_image("JPEG", size=(800, 600))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_image():
    # RGBA image -> should convert and flatten to RGB without alpha
    img_bytes = create_test_image("PNG", size=(500, 500), mode="RGBA", color=(0, 255, 0, 128))
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.format == "JPEG"


def test_compress_palette_image():
    # Palette image (P mode)
    img_bytes = create_test_image("PNG", size=(400, 400), mode="P")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


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
        files={"file": ("invalid.jpg", b"not-an-image-payload", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 50)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"x" * 100, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
