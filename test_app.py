import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400


def test_compress_small_jpeg():
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)
    assert out_img.mode == "RGB"


def test_compress_large_jpeg():
    img = Image.new("RGB", (3000, 2000), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1066)
    assert out_img.mode == "RGB"


def test_compress_rgba_png():
    img = Image.new("RGBA", (2000, 1500), color=(0, 0, 255, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("rgba.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1200)
    assert out_img.mode == "RGB"


def test_compress_palette_png():
    img = Image.new("P", (1800, 1200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("palette.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1066)
    assert out_img.mode == "RGB"
