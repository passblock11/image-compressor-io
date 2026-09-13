import io
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def create_test_image(width=2000, height=1500, mode="RGB", fmt="JPEG"):
    img = Image.new(mode, (width, height), color=(255, 0, 0) if mode != "L" else 128)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid():
    img_bytes = create_test_image(2000, 1500)
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200


def test_compress_small_image():
    img_bytes = create_test_image(800, 600)
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_image():
    img_bytes = create_test_image(2000, 1500, mode="RGBA", fmt="PNG")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("bad.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large():
    mock_file = MagicMock()
    mock_file.file.read.return_value = b"x" * (MAX_FILE_SIZE + 1)
    import pytest
    from fastapi import HTTPException

    from app import compress

    with pytest.raises(HTTPException) as exc_info:
        compress(file=mock_file)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "File too large. Max allowed size is 100 MB"
