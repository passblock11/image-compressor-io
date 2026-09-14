import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def create_test_image(format="JPEG", size=(2000, 1500), mode="RGB", color=(255, 0, 0)):
    buf = io.BytesIO()
    img = Image.new(mode, size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_success():
    jpeg_bytes = create_test_image("JPEG", (2400, 1600))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1066


def test_compress_png_rgba_success():
    png_bytes = create_test_image("PNG", (800, 600), mode="RGBA", color=(0, 255, 0, 128))
    response = client.post(
        "/compress",
        files={"file": ("test.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600
    assert out_img.mode == "RGB"


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
        files={"file": ("bad.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large():
    # Construct bytes exceeding MAX_FILE_SIZE
    large_bytes = b"0" * (MAX_FILE_SIZE + 1)
    response = client.post(
        "/compress",
        files={"file": ("large.bin", large_bytes, "application/octet-stream")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
