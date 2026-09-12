import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_jpeg():
    # Small image (800x600) should not be upscaled
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_large_jpeg():
    # Large image (3000x2000) should be resized to max width 1600 maintaining aspect ratio
    img = Image.new("RGB", (3000, 2000), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height in (1066, 1067)


def test_compress_rgba_png():
    # RGBA PNG should be converted/flattened to JPEG sRGB
    img = Image.new("RGBA", (2000, 1000), color=(0, 0, 255, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf.getvalue(), "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height in (800, 801)
    assert out_img.mode in ("RGB", "L")


def test_compress_cmyk():
    # CMYK image should be converted to sRGB JPEG
    img = Image.new("CMYK", (2000, 1000), color=(100, 50, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("cmyk.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.mode == "RGB"


def test_compress_grayscale_la():
    # Grayscale image with alpha channel
    img = Image.new("LA", (1000, 1000), color=(128, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("la.png", buf.getvalue(), "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1000


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_file_too_large():
    # Create mock large file payload exceeding MAX_FILE_SIZE
    large_bytes = b"0" * (MAX_FILE_SIZE + 10)
    response = client.post(
        "/compress",
        files={"file": ("huge.jpg", large_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"not an image data", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"
