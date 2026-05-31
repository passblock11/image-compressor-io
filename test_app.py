from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image
import pytest

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    # Create a small valid JPEG
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    files = {'file': ('test.jpg', img_byte_arr, 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_large_image_resize():
    # Create an image larger than MAX_WIDTH (1600)
    img = Image.new('RGB', (2000, 1000), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    files = {'file': ('large.jpg', img_byte_arr, 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200

    # Verify resized dimensions
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800

def test_compress_empty_file():
    files = {'file': ('empty.jpg', b'', 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_compress_invalid_image():
    files = {'file': ('invalid.txt', b'not an image', 'text/plain')}
    response = client.post("/compress", files=files)
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_compress_transparency():
    # Create an RGBA image
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {'file': ('transparent.png', img_byte_arr, 'image/png')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Should be converted to RGB
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.mode == "RGB"
