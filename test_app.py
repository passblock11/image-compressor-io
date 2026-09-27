import io

from fastapi.testclient import TestClient
from PIL import Image

import app

client = TestClient(app.app)


def create_test_image(width=3000, height=2000, color=(255, 0, 0), format="JPEG"):
    buf = io.BytesIO()
    img = Image.new("RGB" if format == "JPEG" else "RGBA", (width, height), color)
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    img_bytes = create_test_image(width=2000, height=1000, format="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800


def test_compress_small_jpeg():
    img_bytes = create_test_image(width=800, height=600, format="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_png_rgba():
    img_bytes = create_test_image(width=2000, height=1000, format="PNG")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.mode == "RGB"


def test_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    response = client.post("/compress", files={"file": ("bad.jpg", b"not an image", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large(monkeypatch):
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 100)
    img_bytes = create_test_image(width=200, height=200, format="JPEG")
    response = client.post("/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
