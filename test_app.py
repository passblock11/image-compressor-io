import io
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app, compress

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_file_too_large():
    mock_upload = MagicMock()
    mock_upload.file.seek = MagicMock()
    mock_upload.file.tell = MagicMock(return_value=MAX_FILE_SIZE + 1)

    with pytest.raises(HTTPException) as exc_info:
        compress(mock_upload)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "File too large. Max allowed size is 100 MB"


def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("test.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_small_image():
    # Create small 800x600 image
    img = Image.new("RGB", (800, 600), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)
    assert out_img.format == "JPEG"


def test_compress_large_image():
    # Create large 3000x2000 image
    img = Image.new("RGB", (3000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("large.jpg", buf.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    # 2000 * (1600 / 3000) = 1066.666... -> rounds to 1067
    assert out_img.size == (1600, 1067)
    assert out_img.format == "JPEG"


def test_compress_rgba_image():
    # Create RGBA PNG image
    img = Image.new("RGBA", (2000, 1000), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("rgba.png", buf.getvalue(), "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_grayscale_alpha_image():
    # Create LA (grayscale with alpha) PNG image
    img = Image.new("LA", (2000, 1000), color=(128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("la.png", buf.getvalue(), "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"


def test_compress_cmyk_image():
    # Create CMYK JPEG image (4 bands, no alpha)
    img = Image.new("CMYK", (2000, 1000), color=(100, 50, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post("/compress", files={"file": ("cmyk.jpg", buf.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 800)
    assert out_img.format == "JPEG"
