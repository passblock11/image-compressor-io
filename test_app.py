import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image_resizes(client):
    img = Image.new("RGB", (2400, 1200), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.size == (1600, 800)
    assert output_img.format == "JPEG"


def test_compress_small_image_no_upscale(client):
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.size == (800, 600)


def test_compress_rgba_converted_to_rgb(client):
    img = Image.new("RGBA", (1000, 1000), color=(50, 100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("alpha.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.mode == "RGB"
    assert output_img.format == "JPEG"


def test_compress_palette_converted_to_rgb(client):
    img = Image.new("P", (500, 500))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("palette.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.mode == "RGB"


def test_compress_empty_file_returns_400(client):
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image_returns_400(client):
    response = client.post(
        "/compress",
        files={"file": ("invalid.txt", b"this is not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(client, monkeypatch):
    import app as app_module

    # Temporarily set MAX_FILE_SIZE to 10 bytes for testing
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", b"0123456789extra_bytes", "image/jpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
