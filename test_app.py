import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_success():
    # Create a 2000x1500 JPEG image (width > MAX_WIDTH of 1600)
    img = Image.new("RGB", (2000, 1500), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1200)


def test_compress_png_rgba_success():
    # Create a 2000x1500 RGBA PNG image
    img = Image.new("RGBA", (2000, 1500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify mode converted to RGB and resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1600, 1200)


def test_compress_small_image_no_upscale():
    # Create an 800x600 image (width <= 1600)
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )

    assert response.status_code == 400


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Set MAX_FILE_SIZE to 10 bytes for testing limit
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"123456789012345", "image/jpeg")}
    )

    assert response.status_code in (400, 413)
