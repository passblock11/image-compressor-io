import io

import pytest
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
    # Create image with width > 1600
    img = Image.new("RGB", (2400, 1200), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Check output image dimensions have scaled down proportionally
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)


def test_compress_small_jpeg_not_upscaled():
    # Images with width <= 1600 should maintain original dimensions
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


@pytest.mark.parametrize("mode", ["RGBA", "P", "L", "LA"])
def test_compress_non_rgb_modes(mode):
    # Verify non-RGB modes are properly converted to RGB and saved as JPEG
    img = Image.new(mode, (400, 300))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": (f"test_{mode.lower()}.png", buf, "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (400, 300)


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_corrupt_file():
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", io.BytesIO(b"not an image"), "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Set MAX_FILE_SIZE small for testing 413 exception
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 50)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", io.BytesIO(b"A" * 100), "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
