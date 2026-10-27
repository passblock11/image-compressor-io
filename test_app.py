import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(mode="RGB", size=(2000, 2000), fmt="JPEG"):
    img = Image.new(mode, size, color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_large_image():
    img_bytes = create_test_image(size=(2000, 1500))
    response = client.post(
        "/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Verify resized image dimensions
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 1200


def test_compress_small_image():
    img_bytes = create_test_image(size=(800, 600))
    response = client.post(
        "/compress", files={"file": ("small.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_png_rgba():
    img_bytes = create_test_image(mode="RGBA", size=(1800, 1200), fmt="PNG")
    response = client.post(
        "/compress", files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 1600


def test_compress_empty_file():
    response = client.post(
        "/compress", files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post(
        "/compress", files={"file": ("corrupt.jpg", b"not an image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)  # 100 bytes limit
    img_bytes = create_test_image()
    response = client.post(
        "/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
