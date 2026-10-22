import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width: int, height: int, mode: str = "RGB", fmt: str = "JPEG") -> bytes:
    img = Image.new(mode, (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_resize():
    # Large image > 1600px width
    img_bytes = create_test_image(2000, 1000, "RGB", "JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify output dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800


def test_compress_small_jpeg_no_resize():
    # Small image <= 1600px width
    img_bytes = create_test_image(800, 600, "RGB", "JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 800
    assert out_img.size[1] == 600


def test_compress_rgba_png_conversion():
    # PNG with RGBA mode
    img_bytes = create_test_image(1800, 1200, "RGBA", "PNG")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 1600


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("bad.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Set a small MAX_FILE_SIZE to test 413 error without using 100MB RAM
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    data = b"a" * 150
    response = client.post("/compress", files={"file": ("large.jpg", data, "image/jpeg")})
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
