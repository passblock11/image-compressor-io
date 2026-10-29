import io

from fastapi.testclient import TestClient
from PIL import Image

import app
from app import app as fastapi_app

client = TestClient(fastapi_app)


def create_test_image(width=1800, height=1200, fmt="JPEG", mode="RGB"):
    img = Image.new(mode, (width, height), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_dimensions():
    # Width 1800 > 1600 MAX_WIDTH
    img_bytes = create_test_image(width=1800, height=1200)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1066


def test_compress_small_dimensions():
    # Width 800 <= 1600 MAX_WIDTH
    img_bytes = create_test_image(width=800, height=600)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_mode():
    img_bytes = create_test_image(width=500, height=500, fmt="PNG", mode="RGBA")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Set MAX_FILE_SIZE artificially low for test
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 100)
    img_bytes = create_test_image(width=500, height=500)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
