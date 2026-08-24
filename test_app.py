import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_resize():
    # Large JPEG image (2400x1600)
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

    # Verify resized image dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1066


def test_compress_rgba_png_conversion():
    # RGBA PNG image (800x600 - smaller than MAX_WIDTH)
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

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600
    assert out_img.mode == "RGB"


def test_compress_empty_file():
    buf = io.BytesIO()
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
        files={"file": ("invalid.txt", buf, "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] in ("Invalid image file", "Upload failed")


def test_compress_file_too_large(monkeypatch):
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
