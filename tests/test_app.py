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

def test_compress_image():
    # Create a small test image
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {"file": ("test.png", img_byte_arr, "image/png")}
    response = client.post("/compress", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify it's a valid JPEG
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"

def test_compress_large_image():
    # Create a large test image (wider than 1600)
    img = Image.new("RGB", (2000, 1000), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    files = {"file": ("test_large.png", img_byte_arr, "image/png")}
    response = client.post("/compress", files=files)

    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800

def test_invalid_file():
    files = {"file": ("test.txt", b"not an image", "text/plain")}
    response = client.post("/compress", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_empty_file():
    files = {"file": ("empty.png", b"", "image/png")}
    response = client.post("/compress", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"
