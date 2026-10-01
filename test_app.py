import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width, height, mode="RGB", color="red", fmt="JPEG"):
    img = Image.new(mode, (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    img_bytes = create_test_image(2000, 1000, mode="RGB", fmt="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized dimensions
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 800


def test_compress_small_jpeg_no_upscale():
    img_bytes = create_test_image(800, 600, mode="RGB", fmt="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("small.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 800
    assert res_img.height == 600


def test_compress_valid_png_rgba():
    img_bytes = create_test_image(2000, 1000, mode="RGBA", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 800


def test_compress_valid_png_la():
    img_bytes = create_test_image(1200, 800, mode="LA", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("la.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1200
    assert res_img.height == 800


def test_compress_cmyk_jpeg():
    img_bytes = create_test_image(1000, 1000, mode="CMYK", fmt="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("cmyk.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


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
        files={"file": ("invalid.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)
    img_bytes = create_test_image(100, 100)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
