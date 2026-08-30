import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_image_resized():
    # Create an image wider than MAX_WIDTH (1600)
    img = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800


def test_compress_valid_image_small():
    # Image within MAX_WIDTH limit
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_image():
    img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("rgba.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("text.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large():
    # Simulate payload larger than MAX_FILE_SIZE
    large_payload = b"0" * (MAX_FILE_SIZE + 1)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", large_payload, "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
