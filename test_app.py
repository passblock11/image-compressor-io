import pytest
from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    # Create a simple valid JPEG image
    img_data = io.BytesIO()
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_data, format='JPEG')
    img_data.seek(0)

    response = client.post("/compress", files={"file": ("test.jpg", img_data, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify image is valid and dimensions are correct
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (100, 100)

def test_compress_large_image_resizing():
    # Create an image larger than MAX_WIDTH (1600)
    img_data = io.BytesIO()
    img = Image.new('RGB', (2000, 1000), color='blue')
    img.save(img_data, format='JPEG')
    img_data.seek(0)

    response = client.post("/compress", files={"file": ("large.jpg", img_data, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    # Aspect ratio preserved: 1000 * (1600 / 2000) = 800
    assert out_img.size[1] == 800

def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]

def test_compress_png_transparency():
    # Create a PNG with transparency (RGBA)
    img_data = io.BytesIO()
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img.save(img_data, format='PNG')
    img_data.seek(0)

    response = client.post("/compress", files={"file": ("trans.png", img_data, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB" # JPEG should be RGB
    # Verify it was flattened (background should be white-ish where it was transparent)
    # The red is (255, 0, 0, 128) flattened on (255, 255, 255, 255)
    # Result should be approx (255, 127, 127)
    pixel = out_img.getpixel((50, 50))
    assert pixel[0] == 255
    assert 120 <= pixel[1] <= 135
    assert 120 <= pixel[2] <= 135
