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
        "/compress", files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400


def test_compress_invalid_image():
    response = client.post(
        "/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400


def test_compress_resize_large_image():
    # Create 2000x1000 image
    img = Image.new("RGB", (2000, 1000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)


def test_compress_small_image():
    # Create 800x600 image
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_image():
    # Create RGBA image with transparency
    img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("transparent.png", buf.getvalue(), "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1000, 1000)
    assert out_img.mode == "RGB"
