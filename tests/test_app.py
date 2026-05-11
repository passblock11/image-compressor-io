import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import app, MAX_FILE_SIZE

client = TestClient(app)

def create_test_image(size=(2000, 2000), mode='RGB', format='JPEG'):
    img = Image.new(mode, size, color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=format)
    return img_byte_arr.getvalue()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    img_bytes = create_test_image()
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify output image size
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.width <= 1600

def test_compress_max_width_enforced():
    img_bytes = create_test_image(size=(3000, 1000))
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    # Height should be 1600 * (1000/3000) = 533.33 -> 533
    assert out_img.height == 533

def test_compress_small_image_not_upscaled():
    img_bytes = create_test_image(size=(800, 600))
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600

def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_file_size_limit(monkeypatch):
    # Temporarily lower MAX_FILE_SIZE for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    img_bytes = b"a" * 101
    response = client.post("/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]

def test_transparency_handling():
    # Create RGBA PNG with transparency
    img_bytes = create_test_image(mode='RGBA', format='PNG')
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"

def test_palette_mode_handling():
    # Create P mode PNG
    img_bytes = create_test_image(mode='P', format='PNG')
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
