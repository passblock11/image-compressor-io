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
    img = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw = buf.getvalue()

    response = client.post(
        "/compress", files={"file": ("test.jpg", io.BytesIO(raw), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_small_image_no_upscale():
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw = buf.getvalue()

    response = client.post(
        "/compress", files={"file": ("test.jpg", io.BytesIO(raw), "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_image():
    img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    response = client.post(
        "/compress", files={"file": ("test.png", io.BytesIO(raw), "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1600, 800)


def test_compress_empty_file():
    response = client.post(
        "/compress", files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", io.BytesIO(b"not an image"), "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", io.BytesIO(b"1234567890123"), "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
