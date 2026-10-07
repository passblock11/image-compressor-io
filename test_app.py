import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    large_payload = b"x" * 20
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", large_payload, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}


def test_compress_valid_jpeg():
    img = Image.new("RGB", (2000, 1000), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    payload = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", payload, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (1600, 800)


def test_compress_rgba_png():
    img = Image.new("RGBA", (800, 600), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", payload, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (800, 600)
    assert out_img.mode == "RGB"
