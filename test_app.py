import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(mode="RGB", size=(800, 600), format="JPEG"):
    buf = io.BytesIO()
    img = Image.new(mode, size, color=(120, 150, 200) if mode != "L" else 128)
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_regular_image():
    image_bytes = create_test_image("RGB", (800, 600), format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify returned image
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (800, 600)


def test_compress_large_image_resizes():
    # Width 2400 > MAX_WIDTH (1600)
    image_bytes = create_test_image("RGB", (2400, 1200), format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", image_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (1600, 800)


def test_compress_rgba_and_palette_modes():
    # RGBA mode PNG
    rgba_bytes = create_test_image("RGBA", (500, 500), format="PNG")
    response = client.post(
        "/compress",
        files={"file": ("transparent.png", rgba_bytes, "image/png")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"

    # Palette mode
    p_img = Image.new("P", (400, 400))
    p_buf = io.BytesIO()
    p_img.save(p_buf, format="PNG")
    response = client.post(
        "/compress",
        files={"file": ("palette.png", p_buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200


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
        files={"file": ("corrupt.jpg", b"not-a-valid-image-content", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Set MAX_FILE_SIZE small for test
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    image_bytes = create_test_image("RGB", (200, 200), format="JPEG")
    assert len(image_bytes) > 100

    response = client.post(
        "/compress",
        files={"file": ("toolarge.jpg", image_bytes, "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
