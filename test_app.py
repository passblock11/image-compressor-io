import io

from fastapi.testclient import TestClient
from PIL import Image

import app
from app import app as fastapi_app

client = TestClient(fastapi_app)


def create_test_image(width=2000, height=1500, mode="RGB", fmt="JPEG"):
    img = Image.new(mode, (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_resize():
    img_bytes = create_test_image(2000, 1500, "RGB", "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify dimensions resized to max width 1600 preserving aspect ratio
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 1200


def test_compress_small_jpeg_no_upscale():
    img_bytes = create_test_image(1200, 800, "RGB", "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1200, 800)


def test_compress_rgba_png_conversion():
    img_bytes = create_test_image(1000, 800, "RGBA", "PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1000, 800)


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large(monkeypatch):
    # Temporarily set MAX_FILE_SIZE to 10 bytes to test limit
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 10)
    img_bytes = create_test_image(100, 100, "RGB", "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
