import io

from fastapi.testclient import TestClient
from PIL import Image

import app
from app import app as fastapi_app

client = TestClient(fastapi_app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_empty_file():
    response = client.post(
        "/compress", files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 10)
    response = client.post(
        "/compress",
        files={"file": ("too_large.jpg", b"123456789012345", "image/jpeg")},
    )
    assert response.status_code == 413
    assert (
        response.json()["detail"]
        == "File too large. Max allowed size is 100 MB"
    )


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={
            "file": (
                "invalid.jpg",
                b"not an image payload",
                "image/jpeg",
            )
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_large_jpeg_image():
    img = Image.new("RGB", (2400, 1600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 1066


def test_compress_small_jpeg_image():
    img = Image.new("RGB", (800, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_png_image():
    img = Image.new("RGBA", (1000, 1000), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("alpha.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"


def test_compress_palette_png_image():
    img = Image.new("P", (1200, 800))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("palette.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "JPEG"
    assert out_img.mode == "RGB"
