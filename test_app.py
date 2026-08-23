from fastapi.testclient import TestClient
from app import app
from PIL import Image
import io
import pytest

client = TestClient(app)

def create_test_image_bytes(width=2000, height=1000, format="JPEG", mode="RGB"):
    img = Image.new(mode, (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_jpeg_resize():
    img_bytes = create_test_image_bytes(2000, 1000, "JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)

def test_compress_small_image_no_resize():
    img_bytes = create_test_image_bytes(1000, 500, "JPEG")
    response = client.post("/compress", files={"file": ("small.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1000, 500)

def test_compress_rgba_png():
    img_bytes = create_test_image_bytes(2000, 1000, "PNG", mode="RGBA")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.mode == "RGB"

def test_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_invalid_image():
    response = client.post("/compress", files={"file": ("bad.jpg", b"not an image", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_file_too_large():
    # Test checking size error logic
    large_bytes = b"0" * (100 * 1024 * 1024 + 1)
    response = client.post("/compress", files={"file": ("large.jpg", large_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
