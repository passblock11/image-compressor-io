import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(mode="RGB", size=(100, 100), fmt="JPEG"):
    img = Image.new(mode, size, color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    img_bytes = create_test_image("RGB", (1000, 800), "JPEG")
    response = client.post(
        "/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_compress_large_image_resize():
    img_bytes = create_test_image("RGB", (2000, 1000), "JPEG")
    response = client.post(
        "/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 800


def test_compress_rgba_image():
    img_bytes = create_test_image("RGBA", (500, 500), "PNG")
    response = client.post(
        "/compress", files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post(
        "/compress", files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)
    img_bytes = create_test_image("RGB", (100, 100), "JPEG")
    response = client.post(
        "/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
