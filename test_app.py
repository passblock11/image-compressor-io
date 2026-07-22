import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app import app, MAX_FILE_SIZE


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image(client):
    # Generate a large 2000x1000 RGBA image (transparency)
    im = Image.new("RGBA", (2000, 1000), "red")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", png_bytes, "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify the image is indeed JPEG and resized to max width 1600
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.format == "JPEG"
    assert output_img.size[0] == 1600
    assert output_img.size[1] == 800  # Aspect ratio preserved


def test_compress_small_image(client):
    # Generate a 800x600 RGB image (no resizing expected)
    im = Image.new("RGB", (800, 600), "blue")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.format == "JPEG"
    assert output_img.size == (800, 600)  # Dimension should be exactly the same


def test_compress_empty_file(client):
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


def test_compress_too_large_file(client):
    # Create a dummy large file structure
    dummy_bytes = b"\0" * (MAX_FILE_SIZE + 1024)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", dummy_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]


def test_compress_invalid_file(client):
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]


def test_compress_la_mode_image(client):
    # Generate a grey-alpha (LA) image
    im = Image.new("LA", (100, 100), (128, 255))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    la_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("la.png", la_bytes, "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.format == "JPEG"
    assert output_img.size == (100, 100)
