import io

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def create_test_image(width=500, height=500, mode="RGB", format="JPEG"):
    img = Image.new(mode, (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_jpeg():
    img_bytes = create_test_image(width=800, height=600, mode="RGB", format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (800, 600)
    assert res_img.format == "JPEG"


def test_compress_large_jpeg():
    img_bytes = create_test_image(width=3000, height=2000, mode="RGB", format="JPEG")
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (1600, 1066) or res_img.size == (1600, 1067)
    assert res_img.format == "JPEG"


def test_compress_png_rgba():
    img_bytes = create_test_image(width=1000, height=1000, mode="RGBA", format="PNG")
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (1000, 1000)
    assert res_img.format == "JPEG"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"not an image data", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image file"}
