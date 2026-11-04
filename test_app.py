import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def create_image(size=(100, 100), mode="RGB", fmt="JPEG"):
    buf = io.BytesIO()
    img = Image.new(mode, size, color="red")
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_compress_large_jpeg():
    data = create_image((2000, 1000), "RGB", "JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", data, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800


def test_compress_small_jpeg():
    data = create_image((800, 600), "RGB", "JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", data, "image/jpeg")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size == (800, 600)


def test_compress_rgba_png():
    data = create_image((500, 500), "RGBA", "PNG")
    response = client.post("/compress", files={"file": ("test.png", data, "image/png")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_palette_png():
    buf = io.BytesIO()
    img = Image.new("P", (100, 100))
    img.save(buf, format="PNG")
    response = client.post("/compress", files={"file": ("palette.png", buf.getvalue(), "image/png")})
    assert response.status_code == 200
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_empty():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid():
    response = client.post("/compress", files={"file": ("bad.jpg", b"notanimage", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    response = client.post("/compress", files={"file": ("big.jpg", b"x" * 20, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"
