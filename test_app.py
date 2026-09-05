import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width: int, height: int, fmt: str = "JPEG") -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    img_bytes = create_test_image(2000, 1000, "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800


def test_compress_small_jpeg():
    img_bytes = create_test_image(800, 600, "JPEG")
    response = client.post(
        "/compress",
        files={"file": ("small.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 800
    assert output_img.height == 600


def test_compress_png():
    img = Image.new("RGBA", (2000, 1000), color=(200, 100, 50, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/compress",
        files={"file": ("test.png", png_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("invalid.jpg", b"not an image content", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Simulate file size exceeding MAX_FILE_SIZE
    img_bytes = create_test_image(100, 100, "JPEG")

    # Override MAX_FILE_SIZE temporarily to test 413 error
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 50)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
