import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width=1000, height=1000, fmt="JPEG", mode="RGB"):
    img = Image.new(mode, (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_jpeg_image():
    img_bytes = create_test_image(width=800, height=600, fmt="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_large_jpeg_image():
    img_bytes = create_test_image(width=3000, height=2000, fmt="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (1600, 1066)


def test_compress_large_png_rgba_image():
    img_bytes = create_test_image(width=2400, height=1800, fmt="PNG", mode="RGBA")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1600, 1200)


def test_compress_small_png_rgba_image():
    img_bytes = create_test_image(width=800, height=600, fmt="PNG", mode="RGBA")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (800, 600)


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image file content", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 10)
    img_bytes = create_test_image(width=100, height=100)
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
