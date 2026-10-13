import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    # Create image larger than MAX_WIDTH (e.g. 2000x1000)
    img_buf = io.BytesIO()
    Image.new("RGB", (2000, 1000), color="blue").save(img_buf, format="JPEG")
    payload = img_buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", payload, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)


def test_compress_small_jpeg():
    # Create image smaller than MAX_WIDTH (e.g. 800x600)
    img_buf = io.BytesIO()
    Image.new("RGB", (800, 600), color="green").save(img_buf, format="JPEG")
    payload = img_buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", payload, "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_png_rgba():
    # Create RGBA PNG
    img_buf = io.BytesIO()
    Image.new("RGBA", (500, 500), color=(255, 0, 0, 128)).save(img_buf, format="PNG")
    payload = img_buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("transparent.png", payload, "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (500, 500)


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("not_an_image.txt", b"Hello world text payload", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)  # 10 bytes limit

    response = client.post(
        "/compress",
        files={"file": ("too_large.jpg", b"123456789012345", "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}
