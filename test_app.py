import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_dummy_image(width, height, format="JPEG", mode="RGB"):
    img = Image.new(mode, (width, height), color=(100, 150, 200) if mode in ("RGB", "RGBA") else 128)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    image_bytes = create_dummy_image(3000, 2000, format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1066)
    assert out_img.format == "JPEG"


def test_compress_small_image():
    image_bytes = create_dummy_image(800, 600, format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_png_image():
    image_bytes = create_dummy_image(2000, 1000, format="PNG", mode="RGBA")
    response = client.post(
        "/compress",
        files={"file": ("test.png", image_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.mode == "RGB"


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
        files={"file": ("corrupt.jpg", b"not an image content", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Set MAX_FILE_SIZE small for testing limit exception
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    image_bytes = create_dummy_image(200, 200, format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
