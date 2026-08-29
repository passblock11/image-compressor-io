import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


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
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_valid_jpeg_resizing():
    # Create large 2400x1600 image
    img = Image.new("RGB", (2400, 1600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized width is MAX_WIDTH (1600)
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600


def test_compress_png_with_alpha():
    # Create RGBA image
    img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("alpha.png", buf.getvalue(), "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"
    assert res_img.width == 1600


def test_compress_small_image_no_upscale():
    # Create small 800x600 image
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")}
    )

    assert response.status_code == 200
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (800, 600)


def test_compress_file_too_large(monkeypatch):
    # Set MAX_FILE_SIZE low for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", b"x" * 200, "image/jpeg")}
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
