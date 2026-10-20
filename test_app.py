import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(format="JPEG", size=(2000, 1500), mode="RGB"):
    buf = io.BytesIO()
    img = Image.new(mode, size, color="blue")
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_jpeg_success():
    img_bytes = create_test_image("JPEG", size=(2000, 1500))
    response = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Check that image was resized
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 1200


def test_compress_small_image():
    img_bytes = create_test_image("JPEG", size=(800, 600))
    response = client.post("/compress", files={"file": ("small.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 800
    assert output_img.height == 600


def test_compress_rgba_image():
    img_bytes = create_test_image("PNG", size=(2000, 1500), mode="RGBA")
    response = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.mode == "RGB"
    assert output_img.width == 1600


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_image():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 100)
    img_bytes = b"x" * 150
    response = client.post("/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
