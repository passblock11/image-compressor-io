import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_dummy_image(width=2000, height=1500, fmt="JPEG", mode="RGB"):
    buf = io.BytesIO()
    img = Image.new(mode, (width, height), color=(100, 150, 200))
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    img_bytes = create_dummy_image(width=2000, height=1000, fmt="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized image
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 800


def test_compress_small_image():
    img_bytes = create_dummy_image(width=800, height=600, fmt="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("small.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 800
    assert res_img.height == 600


def test_compress_rgba_png():
    img_bytes = create_dummy_image(width=1800, height=1200, fmt="PNG", mode="RGBA")
    response = client.post(
        "/compress",
        files={"file": ("transparent.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"
    assert res_img.width == 1600


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"
