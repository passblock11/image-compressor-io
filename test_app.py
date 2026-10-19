import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(format="JPEG", size=(2000, 1000), mode="RGB"):
    img = Image.new(mode, size, color="blue")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_success():
    img_bytes = create_test_image("JPEG", (2000, 1000))
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized width is 1600
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800


def test_compress_small_image():
    img_bytes = create_test_image("JPEG", (800, 600))
    response = client.post("/compress", files={"file": ("small.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_png():
    img_bytes = create_test_image("PNG", (2000, 1000), mode="RGBA")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.width == 1600


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    img_bytes = create_test_image("JPEG", (500, 500))
    assert len(img_bytes) > 100
    response = client.post("/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}
