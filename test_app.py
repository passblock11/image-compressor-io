import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    # Create a JPEG image larger than 1600 px width
    img = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify compressed image is resized
    compressed_img = Image.open(io.BytesIO(response.content))
    assert compressed_img.width == 1600
    assert compressed_img.height == 800


def test_compress_valid_rgba_png():
    # Create an RGBA PNG image
    img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    compressed_img = Image.open(io.BytesIO(response.content))
    assert compressed_img.width == 800
    assert compressed_img.height == 600


def test_compress_empty_file():
    buf = io.BytesIO(b"")
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    buf = io.BytesIO(b"not an image content")
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] in ("Invalid image file", "Upload failed")


def test_compress_file_too_large(monkeypatch):
    # Set limit low to test 413 error
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    buf = io.BytesIO(b"x" * 20)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
