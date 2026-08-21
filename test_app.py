import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


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
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large():
    # 100 MB + 1 byte
    large_data = b"0" * (100 * 1024 * 1024 + 1)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", large_data, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"


def test_compress_large_image():
    # 3000 x 2000 image
    img = Image.new("RGB", (3000, 2000), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", data, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] in (1066, 1067)
    assert out_img.format == "JPEG"


def test_compress_small_image():
    # 800 x 600 image
    img = Image.new("RGB", (800, 600), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", data, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)
    assert out_img.format == "JPEG"


def test_compress_rgba_image():
    # 2000 x 1000 RGBA image with transparency
    img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", data, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_grayscale_image():
    # 1200 x 900 Grayscale image
    img = Image.new("L", (1200, 900), color=120)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test_gray.jpg", data, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1200, 900)
    assert out_img.format == "JPEG"
