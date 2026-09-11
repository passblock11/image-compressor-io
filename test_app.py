import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_resize():
    # Create an image wider than 1600px
    img = Image.new("RGB", (2000, 1000), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify output image dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800


def test_compress_small_image_no_resize():
    # Create an image smaller than 1600px
    img = Image.new("RGB", (800, 600), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_png():
    # Create an RGBA image with transparency
    img = Image.new("RGBA", (1800, 900), color=(0, 0, 255, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800
    assert out_img.mode == "RGB"


def test_compress_grayscale_la_png():
    # Create a LA grayscale image with alpha
    img = Image.new("LA", (500, 500), color=(128, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test_la.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 500
    assert out_img.height == 500


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", b"not an image file data", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 5)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"a" * 10, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
