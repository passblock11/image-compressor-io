import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    # Create an image wider than 1600px (e.g., 2000x1000)
    img = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized width is 1600
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)


def test_compress_small_image():
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_image():
    img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("alpha.png", buf, "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_empty_file():
    buf = io.BytesIO(b"")

    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    buf = io.BytesIO(b"this is not an image file payload")

    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", buf, "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_oversized_file(monkeypatch):
    # Temporarily set MAX_FILE_SIZE to 10 bytes for testing
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)

    buf = io.BytesIO(b"0123456789ABCDEF")  # 16 bytes > 10 bytes

    response = client.post(
        "/compress",
        files={"file": ("big.jpg", buf, "image/jpeg")}
    )

    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
