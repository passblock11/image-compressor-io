import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_large():
    img = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", buf, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_jpeg_small():
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", buf, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)
    assert out_img.format == "JPEG"


def test_compress_rgba_png():
    img = Image.new("RGBA", (1800, 1200), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("test.png", buf, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1066)
    assert out_img.mode == "RGB"


def test_compress_empty_file():
    buf = io.BytesIO(b"")
    response = client.post("/compress", files={"file": ("empty.jpg", buf, "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    buf = io.BytesIO(b"not an image data content")
    response = client.post("/compress", files={"file": ("invalid.txt", buf, "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large():
    buf = io.BytesIO(b"x" * (100 * 1024 * 1024 + 1))
    response = client.post("/compress", files={"file": ("large.jpg", buf, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
