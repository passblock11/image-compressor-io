import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(mode="RGB", size=(2000, 1500), fmt="JPEG"):
    img = Image.new(mode, size, color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_normal_image():
    img_buf = create_test_image(size=(2000, 1500))
    response = client.post("/compress", files={"file": ("test.jpg", img_buf, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1200)


def test_compress_small_image():
    img_buf = create_test_image(size=(800, 600))
    response = client.post("/compress", files={"file": ("test.jpg", img_buf, "image/jpeg")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_image():
    img_buf = create_test_image(mode="RGBA", size=(2000, 1500), fmt="PNG")
    response = client.post("/compress", files={"file": ("test.png", img_buf, "image/png")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1600, 1200)


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("bad.txt", io.BytesIO(b"not an image"), "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)
    img_buf = create_test_image(size=(100, 100))
    response = client.post("/compress", files={"file": ("large.jpg", img_buf, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
