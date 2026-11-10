import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)

def create_image(mode="RGB", size=(2000, 1500), fmt="JPEG"):
    buf = io.BytesIO()
    img = Image.new(mode, size, color=(200, 100, 50) if mode == "RGB" else 128)
    if fmt == "PNG" and mode == "RGBA":
        img = Image.new("RGBA", size, color=(200, 100, 50, 255))
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()

def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "Image compression API running"}

def test_compress_large_image():
    img_bytes = create_image(size=(2400, 1800))
    res = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(res.content))
    assert out_img.size == (1600, 1200)

def test_compress_small_image():
    img_bytes = create_image(size=(800, 600))
    res = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(res.content))
    assert out_img.size == (800, 600)

def test_compress_rgba():
    img_bytes = create_image(mode="RGBA", size=(1800, 1200), fmt="PNG")
    res = client.post("/compress", files={"file": ("test.png", img_bytes, "image/png")})
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    out_img = Image.open(io.BytesIO(res.content))
    assert out_img.mode == "RGB"
    assert out_img.size == (1600, int(1200 * (1600 / 1800)))

def test_empty_file():
    res = client.post("/compress", files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert res.status_code == 400
    assert res.json()["detail"] == "Empty file"

def test_invalid_image():
    res = client.post("/compress", files={"file": ("invalid.jpg", b"not-an-image", "image/jpeg")})
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid image file"

def test_file_too_large(monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE", 100)
    img_bytes = create_image(size=(200, 200))
    assert len(img_bytes) > 100
    res = client.post("/compress", files={"file": ("test.jpg", img_bytes, "image/jpeg")})
    assert res.status_code == 413
    assert res.json()["detail"] == "File too large. Max allowed size is 100 MB"
