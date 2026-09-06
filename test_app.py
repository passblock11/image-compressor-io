import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

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
    assert response.json() == {"detail": "Empty file"}


def test_compress_file_too_large():
    # Construct a dummy payload exceeding MAX_FILE_SIZE without allocating excessive memory
    large_payload = b"0" * (MAX_FILE_SIZE + 1)
    response = client.post(
        "/compress", files={"file": ("large.jpg", large_payload, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json() == {
        "detail": "File too large. Max allowed size is 100 MB"
    }


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("test.txt", b"not an image file", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_large_jpeg():
    # Create a 3000x2000 JPEG
    img = Image.new("RGB", (3000, 2000), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized image dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1066  # 2000 * 1600 / 3000


def test_compress_small_jpeg():
    # Create an 800x600 JPEG (smaller than MAX_WIDTH)
    img = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_png_rgba():
    # Create an RGBA PNG
    img = Image.new("RGBA", (2000, 1500), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("rgba.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.mode == "RGB"
