import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(mode="RGB", size=(2000, 1500), fmt="JPEG"):
    img = Image.new(mode, size, color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_large():
    img_bytes = create_test_image(mode="RGB", size=(3000, 2000), fmt="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size[0] == 1600
    assert res_img.mode == "RGB"


def test_compress_png_rgba():
    img_bytes = create_test_image(mode="RGBA", size=(2000, 2000), fmt="PNG")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size[0] == 1600
    assert res_img.mode == "RGB"


def test_compress_small_image_no_resize():
    img_bytes = create_test_image(mode="RGB", size=(800, 600), fmt="JPEG")
    response = client.post("/compress", files={"file": ("small.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (800, 600)


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", b"invalid_data_longer_than_zero_bytes", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    data = b"x" * 200
    response = client.post("/compress", files={"file": ("large.jpg", data, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
