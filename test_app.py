import io

from fastapi.testclient import TestClient
from PIL import Image

import app

client = TestClient(app.app)


def create_test_image(size=(100, 100), mode="RGB", fmt="JPEG"):
    buf = io.BytesIO()
    img = Image.new(
        mode,
        size,
        color=(255, 0, 0) if mode != "RGBA" else (255, 0, 0, 128),
    )
    if fmt == "JPEG" and mode == "RGBA":
        img = img.convert("RGB")
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_image():
    img_bytes = create_test_image(size=(800, 600))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (800, 600)
    assert res_img.format == "JPEG"


def test_compress_large_image_resizing():
    img_bytes = create_test_image(size=(3200, 1600))
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (1600, 800)


def test_compress_rgba_image():
    img_bytes = create_test_image(size=(500, 500), mode="RGBA", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


def test_compress_palette_image():
    img_bytes = create_test_image(size=(200, 200), mode="P", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("test_palette.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large(monkeypatch):
    monkeypatch.setattr(app, "MAX_FILE_SIZE", 10)
    response = client.post(
        "/compress",
        files={"file": ("big.jpg", b"123456789012345", "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
