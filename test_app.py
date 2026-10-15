import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)

def make_test_image_bytes(width, height, mode="RGB", fmt="JPEG"):
    img = Image.new(mode, (width, height), color=(200, 100, 50))
    buf = io.BytesIO()
    if fmt == "JPEG" and mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(buf, format=fmt)
    return buf.getvalue()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}

def test_compress_empty_file():
    response = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"

def test_compress_invalid_file():
    response = client.post("/compress", files={"file": ("invalid.txt", b"not an image", "image/jpeg")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"

def test_compress_too_large(monkeypatch):
    monkeypatch.setattr("app.MAX_FILE_SIZE", 10)
    img_bytes = make_test_image_bytes(100, 100)
    response = client.post("/compress", files={"file": ("large.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 413
    assert response.json()["detail"] == "File too large. Max allowed size is 100 MB"

def test_compress_valid_jpeg_resizing():
    # Large image > 1600 width
    img_bytes = make_test_image_bytes(2400, 1200, mode="RGB", fmt="JPEG")
    response = client.post("/compress", files={"file": ("photo.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800
    assert output_img.format == "JPEG"

def test_compress_valid_jpeg_no_resizing():
    # Small image <= 1600 width
    img_bytes = make_test_image_bytes(1000, 500, mode="RGB", fmt="JPEG")
    response = client.post("/compress", files={"file": ("photo.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1000
    assert output_img.height == 500

def test_compress_png_rgba():
    img_bytes = make_test_image_bytes(2000, 1000, mode="RGBA", fmt="PNG")
    response = client.post("/compress", files={"file": ("transparent.png", img_bytes, "image/png")})
    assert response.status_code == 200

    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800
    assert output_img.mode == "RGB"

def test_compress_palette():
    img = Image.new("P", (1800, 900))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    response = client.post("/compress", files={"file": ("palette.png", img_bytes, "image/png")})
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800

def test_compress_cmyk():
    img_bytes = make_test_image_bytes(1800, 900, mode="CMYK", fmt="JPEG")
    response = client.post("/compress", files={"file": ("cmyk.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800

def test_compress_grayscale_la():
    img = Image.new("LA", (1800, 900), (128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    response = client.post("/compress", files={"file": ("gray_alpha.png", img_bytes, "image/png")})
    assert response.status_code == 200
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.width == 1600
    assert output_img.height == 800
