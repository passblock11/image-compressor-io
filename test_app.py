import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(format="JPEG", size=(2000, 1000), mode="RGB", color=(255, 0, 0)):
    buf = io.BytesIO()
    img = Image.new(mode, size, color)
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_large():
    img_bytes = create_test_image(format="JPEG", size=(2400, 1200))
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (1600, 800)


def test_compress_small_image():
    img_bytes = create_test_image(format="JPEG", size=(800, 600))
    response = client.post("/compress", files={"file": ("small.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_png_rgba():
    img_bytes = create_test_image(format="PNG", size=(1000, 1000), mode="RGBA", color=(255, 0, 0, 128))
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"


def test_compress_png_rgba_large():
    img_bytes = create_test_image(format="PNG", size=(2400, 1200), mode="RGBA", color=(255, 0, 0, 128))
    response = client.post("/compress", files={"file": ("test_large.png", img_bytes, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"
    assert out_img.size == (1600, 800)


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Temporarily set MAX_FILE_SIZE smaller for test
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    img_bytes = create_test_image(size=(100, 100))
    response = client.post("/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
