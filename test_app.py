import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width=2000, height=1000, fmt="JPEG", mode="RGB"):
    buf = io.BytesIO()
    img = Image.new(mode, (width, height), color="red")
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    img_bytes = create_test_image(width=2400, height=1200)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 800


def test_compress_small_image():
    img_bytes = create_test_image(width=800, height=400)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 800
    assert res_img.height == 400


def test_compress_rgba_image():
    img_bytes = create_test_image(width=1000, height=500, fmt="PNG", mode="RGBA")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image_file():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    img_bytes = create_test_image(width=200, height=200)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
