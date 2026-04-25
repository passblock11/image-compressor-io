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

def test_compress_jpeg():
    # Create a small RGB image
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_large_image():
    # Create an image larger than MAX_WIDTH (1600)
    img = Image.new("RGB", (2000, 1000), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200

    # Verify the image is resized
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.size[0] == 1600
    assert output_img.size[1] == 800

def test_compress_rgba():
    # Create an RGBA image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", img_byte_arr, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_file_too_large(monkeypatch):
    # Temporarily lower MAX_FILE_SIZE for testing
    import app
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"a" * 20, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
