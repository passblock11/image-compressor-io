import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(size=(2000, 1500), format="JPEG", mode="RGB"):
    img = Image.new(mode, size, color="blue")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    image_bytes = create_test_image(size=(2000, 1500), format="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", image_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.height == 1200


def test_compress_small_jpeg():
    image_bytes = create_test_image(size=(800, 600), format="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", image_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 800
    assert res_img.height == 600


def test_compress_rgba_png():
    image_bytes = create_test_image(size=(1800, 1200), format="PNG", mode="RGBA")
    response = client.post("/compress", files={"file": ("test.png", image_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.width == 1600
    assert res_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Empty file"}


def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("bad.jpg", b"invalid data", "image/jpeg")})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}


def test_compress_file_too_large(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)
    image_bytes = create_test_image(size=(100, 100), format="JPEG")
    response = client.post("/compress", files={"file": ("large.jpg", image_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large. Max allowed size is 100 MB"}
