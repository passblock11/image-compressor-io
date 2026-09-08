import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    # Create a 2000x1000 JPEG
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

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800


def test_compress_small_jpeg():
    # Create an 800x600 JPEG
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_png():
    # Create an RGBA image
    img = Image.new("RGBA", (1800, 1200), color=(255, 0, 0, 128))
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
    assert out_img.size[0] == 1600


def test_compress_empty_file():
    buf = io.BytesIO(b"")
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    buf = io.BytesIO(b"not an image content")
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", buf, "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large():
    # Exceed MAX_FILE_SIZE logically by sending large file
    large_buf = io.BytesIO(b"x" * (MAX_FILE_SIZE + 1))
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", large_buf, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
