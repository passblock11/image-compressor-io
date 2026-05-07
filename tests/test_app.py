import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", img_byte_arr, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_max_width_enforcement():
    img = Image.new('RGB', (2000, 1000), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", img_byte_arr, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800

def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("not_image.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_compress_file_size_limit(monkeypatch):
    from app import MAX_FILE_SIZE
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10) # 10 bytes

    img = Image.new('RGB', (10, 10), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", img_byte_arr, "image/jpeg")})
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]

def test_compress_transparency_handling():
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    response = client.post("/compress", files={"file": ("test.png", img_byte_arr, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_various_input_formats():
    # Test PNG
    img = Image.new('RGB', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    response = client.post("/compress", files={"file": ("test.png", img_byte_arr, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
