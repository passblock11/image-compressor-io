import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_jpeg():
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("test.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_large_jpeg_resize():
    img = Image.new("RGB", (3200, 2400), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("large.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1200)


def test_compress_rgba_png_conversion():
    img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("test.png", buf, "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_palette_image():
    img = Image.new("P", (400, 400))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress", files={"file": ("palette.png", buf, "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_file_too_large(monkeypatch):
    # Temporarily set MAX_FILE_SIZE to 10 bytes to test limit without allocating 100MB
    import app as app_module

    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={
            "file": (
                "large.jpg",
                io.BytesIO(b"123456789012345"),
                "image/jpeg",
            )
        },
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
