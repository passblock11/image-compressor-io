import io

from fastapi.testclient import TestClient
from PIL import Image

import app

client = TestClient(app.app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    img = Image.new("RGB", (2000, 1500), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", buf, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0

    # Verify compressed image is valid JPEG and resized correctly
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200


def test_compress_rgba_png():
    img = Image.new("RGBA", (2000, 1500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("test.png", buf, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200
    assert out_img.mode == "RGB"


def test_compress_small_image():
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("small.jpg", buf, "image/jpeg")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 100)  # 100 bytes limit
    img_data = b"x" * 200
    response = client.post("/compress", files={"file": ("large.jpg", img_data, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"


def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image data", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"
