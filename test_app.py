import io

from fastapi.testclient import TestClient
from PIL import Image

import app as app_module
from app import app

client = TestClient(app)


def create_test_image(width=2000, height=1000, mode="RGB", fmt="JPEG"):
    buf = io.BytesIO()
    if mode == "LA":
        img = Image.new("LA", (width, height), (128, 255))
    elif mode == "RGBA":
        img = Image.new("RGBA", (width, height), (255, 0, 0, 128))
    elif mode == "P":
        img = Image.new("P", (width, height))
    else:
        img = Image.new("RGB", (width, height), color="red")

    img.save(buf, format=fmt)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    raw = create_test_image(width=2400, height=1200, mode="RGB", fmt="JPEG")
    response = client.post("/compress", files={"file": ("test.jpg", raw, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert out_img.size[1] == 800


def test_compress_small_jpeg_no_upscale():
    raw = create_test_image(width=800, height=400, mode="RGB", fmt="JPEG")
    response = client.post("/compress", files={"file": ("small.jpg", raw, "image/jpeg")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 800
    assert out_img.size[1] == 400


def test_compress_rgba_png():
    raw = create_test_image(width=2000, height=1000, mode="RGBA", fmt="PNG")
    response = client.post("/compress", files={"file": ("test.png", raw, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 1600


def test_compress_palette_png():
    raw = create_test_image(width=2000, height=1000, mode="P", fmt="PNG")
    response = client.post("/compress", files={"file": ("palette.png", raw, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_la_png():
    raw = create_test_image(width=2000, height=1000, mode="LA", fmt="PNG")
    response = client.post("/compress", files={"file": ("la.png", raw, "image/png")})
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("bad.jpg", b"not an image", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_file_too_large(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    raw = create_test_image(width=500, height=500, mode="RGB", fmt="JPEG")
    assert len(raw) > 100

    response = client.post("/compress", files={"file": ("large.jpg", raw, "image/jpeg")})
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
