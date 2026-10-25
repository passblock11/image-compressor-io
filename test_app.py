import io
from PIL import Image
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def create_test_image(width: int, height: int, mode: str = "RGB", fmt: str = "JPEG") -> bytes:
    img = Image.new(mode, (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    img_bytes = create_test_image(2000, 1500, "RGB", "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized image dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200


def test_compress_small_image():
    img_bytes = create_test_image(800, 600, "RGB", "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_png():
    img_bytes = create_test_image(1800, 1200, "RGBA", "PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.width == 1600


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    img_bytes = create_test_image(100, 100, "RGB", "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
