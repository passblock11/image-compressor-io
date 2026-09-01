import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(format="JPEG", size=(800, 600), color="red", mode="RGB"):
    img = Image.new(mode, size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg_under_max_width():
    img_bytes = create_test_image(format="JPEG", size=(800, 600))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify returned image
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (800, 600)


def test_compress_valid_jpeg_over_max_width():
    img_bytes = create_test_image(format="JPEG", size=(2000, 1000))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify returned image resized to max width 1600
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.size == (1600, 800)


def test_compress_png_with_alpha():
    img_bytes = create_test_image(format="PNG", size=(500, 500), mode="RGBA")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"


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
    # Temporarily lower MAX_FILE_SIZE for test
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)

    img_bytes = b"x" * 150
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
