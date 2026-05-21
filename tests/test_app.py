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
    # Create a simple JPEG
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_data = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify it's still a valid image
    result_img = Image.open(io.BytesIO(response.content))
    assert result_img.format == "JPEG"

def test_compress_resize():
    # Create a large image (> 1600 width)
    img = Image.new('RGB', (2000, 1000), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_data = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 200
    result_img = Image.open(io.BytesIO(response.content))
    assert result_img.size[0] == 1600
    # Original aspect ratio was 2:1, so height should be 800
    assert result_img.size[1] == 800

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
        files={"file": ("not_an_image.txt", b"not an image data", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_compress_transparency_handling():
    # Create an RGBA image
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_data = img_byte_arr.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("alpha.png", img_data, "image/png")}
    )
    assert response.status_code == 200
    result_img = Image.open(io.BytesIO(response.content))
    assert result_img.mode == "RGB"
    assert result_img.format == "JPEG"
