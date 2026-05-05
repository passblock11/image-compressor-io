from fastapi.testclient import TestClient
from app import app
import io
import pyvips

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_jpeg():
    # Create a small valid JPEG using pyvips
    img = pyvips.Image.black(100, 100, bands=3)
    img_byte_arr = img.jpegsave_buffer()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify result is a valid image
    result_img = pyvips.Image.new_from_buffer(response.content, "")
    assert result_img.width == 100

def test_compress_max_width():
    # Create an image larger than MAX_WIDTH (1600)
    img = pyvips.Image.black(2000, 1000, bands=3)
    img_byte_arr = img.jpegsave_buffer()

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    result_img = pyvips.Image.new_from_buffer(response.content, "")
    assert result_img.width == 1600
    assert result_img.height == 800

def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]
