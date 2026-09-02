import io

from fastapi.testclient import TestClient
from PIL import Image

from app import MAX_FILE_SIZE, app

client = TestClient(app)


def create_test_image(
    format_name="JPEG",
    size=(1000, 800),
    mode="RGB",
    color=(255, 0, 0)
):
    buf = io.BytesIO()
    img = Image.new(mode, size, color=color)
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_valid_jpeg():
    img_bytes = create_test_image("JPEG", size=(1000, 800))
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (1000, 800)
    assert res_img.format == "JPEG"


def test_compress_large_image_resizes():
    img_bytes = create_test_image("JPEG", size=(2400, 1600))
    response = client.post(
        "/compress",
        files={"file": ("test_large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (1600, 1066) or res_img.size == (1600, 1067)
    assert res_img.width == 1600


def test_compress_rgba_png():
    img_bytes = create_test_image("PNG", size=(800, 600), mode="RGBA", color=(255, 0, 0, 128))
    response = client.post(
        "/compress",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


def test_compress_la_png():
    img_bytes = create_test_image("PNG", size=(800, 600), mode="LA", color=(128, 128))
    response = client.post(
        "/compress",
        files={"file": ("test_la.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"


def test_compress_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_compress_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("corrupt.jpg", b"invalid data", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_compress_oversized_file():
    # Mock file size larger than MAX_FILE_SIZE
    oversized_data = b"x" * (MAX_FILE_SIZE + 1)
    response = client.post(
        "/compress",
        files={"file": ("huge.jpg", oversized_data, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
