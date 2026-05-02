import pytest
from fastapi.testclient import TestClient
from app import app
import io
from PIL import Image

client = TestClient(app)

def create_test_image(width, height, format='JPEG', mode='RGB'):
    file = io.BytesIO()
    image = Image.new(mode, (width, height), color='red')
    image.save(file, format)
    file.seek(0)
    return file

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_valid_image():
    img_file = create_test_image(100, 100)
    files = {'file': ('test.jpg', img_file, 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_compress_large_image_resizing():
    # MAX_WIDTH is 1600
    width, height = 2000, 1000
    img_file = create_test_image(width, height)
    files = {'file': ('test.jpg', img_file, 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200

    # Check dimensions of returned image
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800 # (1000 * 1600 / 2000)

def test_compress_small_image_no_upscale():
    width, height = 800, 400
    img_file = create_test_image(width, height)
    files = {'file': ('test.jpg', img_file, 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 400

def test_compress_rgba_flattening():
    img_file = create_test_image(100, 100, format='PNG', mode='RGBA')
    files = {'file': ('test.png', img_file, 'image/png')}
    response = client.post("/compress", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"

def test_empty_file():
    files = {'file': ('empty.jpg', b'', 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_invalid_image():
    files = {'file': ('not_an_image.txt', b'this is not an image', 'text/plain')}
    response = client.post("/compress", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_file_too_large(monkeypatch):
    # Mock MAX_FILE_SIZE to be small for testing
    import app
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 10)

    img_file = create_test_image(100, 100)
    files = {'file': ('large.jpg', img_file, 'image/jpeg')}
    response = client.post("/compress", files=files)
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
