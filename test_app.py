import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width=2000, height=1500, mode="RGB", fmt="JPEG"):
    img = Image.new(mode, (width, height), color=(250, 100, 50) if mode != "P" else 1)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_success():
    img_data = create_test_image(width=2000, height=1500)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Check that returned image is valid JPEG and resized
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200


def test_compress_small_image_no_upscale():
    img_data = create_test_image(width=800, height=600)
    response = client.post(
        "/compress",
        files={"file": ("small.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_png():
    img_data = create_test_image(width=2000, height=1000, mode="RGBA", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_data, "image/png")}
    )
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode in ("RGB", "L")  # JPEG doesn't support alpha
    assert out_img.width == 1600


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"not an image file content", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    img_data = create_test_image(width=500, height=500)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_data, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
