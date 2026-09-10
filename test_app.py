import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width=2000, height=1500, mode="RGB", fmt="JPEG"):
    img = Image.new(mode, (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_image():
    # Large JPEG image (> 1600px width)
    img_bytes = create_test_image(width=2000, height=1500)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_compress_large_rgba_image():
    # Large PNG with alpha channel (> 1600px width)
    img_bytes = create_test_image(width=2000, height=1500, mode="RGBA", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("large_rgba.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200


def test_compress_palette_image():
    # Palette mode image (mode P)
    img_bytes = create_test_image(width=2000, height=1500, mode="P", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("palette.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 1600
    assert out_img.height == 1200


def test_compress_small_image():
    # Small JPEG image (<= 1600px width)
    img_bytes = create_test_image(width=800, height=600)
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.width == 800
    assert out_img.height == 600


def test_compress_rgba_image():
    # PNG with alpha channel
    img_bytes = create_test_image(width=1000, height=800, mode="RGBA", fmt="PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


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
        files={"file": ("corrupt.jpg", b"not-an-image-data", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    # Test file exceeding MAX_FILE_SIZE
    img_bytes = create_test_image(width=100, height=100)

    # Temporarily set MAX_FILE_SIZE to smaller size for testing
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 50)

    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
