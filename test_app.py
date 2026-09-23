import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_large():
    # Create large JPEG image 2400x1600
    img = Image.new("RGB", (2400, 1600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized width is 1600
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 1066  # 1600 * (1600/2400)


def test_compress_small_image():
    # Create small JPEG image 800x600
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 800
    assert output_img.height == 600


def test_compress_png_rgba():
    # Create RGBA PNG image 2000x1000
    img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")}
    )
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800
    assert output_img.mode == "RGB"


def test_empty_file():
    buf = io.BytesIO(b"")
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    buf = io.BytesIO(b"not an image content")
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large(monkeypatch):
    # Temporarily set MAX_FILE_SIZE small to test 413 response
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    buf = io.BytesIO(b"123456789012345")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
