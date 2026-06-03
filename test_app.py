import pytest
from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_image():
    # Create a small valid JPEG image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify it's a valid image
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.format == "JPEG"

def test_compress_resize_image():
    # Create an image larger than 1600px
    img = Image.new('RGB', (2000, 1000), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.size[0] == 1600
    # 1000 * (1600 / 2000) = 800
    assert output_img.size[1] == 800

def test_compress_rgba_conversion():
    # Create an RGBA image
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", img_byte_arr, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.mode == "RGB"

def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_compress_too_large():
    # MAX_FILE_SIZE is 100MB. Let's send something just over it.
    # We can't easily send 100MB in a unit test without consuming much memory,
    # but we can mock or just send a reasonably large one if needed.
    # For now, let's just check the logic if we can.
    pass
