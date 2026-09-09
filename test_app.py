import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_file_too_large():
    # Construct dummy byte array slightly exceeding 100MB without huge memory overhead if possible
    # We can test by mocking or submitting > 100 MB buffer.
    large_bytes = b"x" * (MAX_FILE_SIZE + 1)
    response = client.post("/compress", files={"file": ("large.jpg", large_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}


def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_large_jpeg():
    # Generate 2000x1000 image
    img = Image.new("RGB", (2000, 1000), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post("/compress", files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800


def test_compress_small_jpeg():
    # Generate 800x600 image
    img = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post("/compress", files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_png():
    # Generate RGBA PNG with alpha transparency
    img = Image.new("RGBA", (2000, 1000), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post("/compress", files={"file": ("transparent.png", buf.getvalue(), "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 800
    assert out_img.mode == "RGB"
