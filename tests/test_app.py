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
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'JPEG')
    file.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", file, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_large_image_resizing():
    # Create a large JPEG
    file = io.BytesIO()
    image = Image.new('RGB', (2000, 1000), color='blue')
    image.save(file, 'JPEG')
    file.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", file, "image/jpeg")})
    assert response.status_code == 200

    # Check dimensions of the result
    img = Image.open(io.BytesIO(response.content))
    assert img.width == 1600
    assert img.height == 800

def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("test.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    # The current app returns "Invalid image file" for UnidentifiedImageError
    assert response.json()["detail"] == "Invalid image file"

def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_compress_transparency():
    # Create an RGBA image
    file = io.BytesIO()
    image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    image.save(file, 'PNG')
    file.seek(0)

    response = client.post("/compress", files={"file": ("test.png", file, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Ensure it's now RGB
    img = Image.open(io.BytesIO(response.content))
    assert img.mode == "RGB"
