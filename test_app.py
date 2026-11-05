import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(width=100, height=100, mode="RGB", color=(255, 0, 0), img_format="JPEG"):
    image = Image.new(mode, (width, height), color=color)
    buf = io.BytesIO()
    image.save(buf, format=img_format)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_success():
    img_data = create_test_image(width=800, height=600, mode="RGB", img_format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (800, 600)


def test_compress_png_with_alpha():
    img_data = create_test_image(
        width=500, height=500, mode="RGBA", color=(0, 255, 0, 128), img_format="PNG"
    )
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_data, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"
    assert out_img.size == (500, 500)


def test_compress_large_image_resizing():
    img_data = create_test_image(width=3200, height=1600, mode="RGB", img_format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", b"not an image file data", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    large_payload = b"A" * 150
    response = client.post(
        "/compress",
        files={"file": ("large.dat", large_payload, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}
