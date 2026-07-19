import io
from fastapi.testclient import TestClient
from PIL import Image
from app import app, MAX_FILE_SIZE

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_small_image():
    # 100x100 black image
    img = Image.new("RGB", (100, 100), color="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    # Check that returned image is valid and has same size
    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (100, 100)


def test_compress_large_image():
    # 2000x1000 red image
    img = Image.new("RGB", (2000, 1000), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.size == (1600, 800)


def test_compress_rgba_image():
    # 100x100 RGBA image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/compress",
        files={"file": ("test.png", buf, "image/png")}
    )
    assert response.status_code == 200

    res_img = Image.open(io.BytesIO(response.content))
    assert res_img.mode == "RGB"
    assert res_img.size == (100, 100)


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_image():
    response = client.post(
        "/compress",
        files={"file": ("test.jpg", b"not-an-image", "image/jpeg")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_oversized_file():
    # Attempt to upload an oversized byte stream.
    # To avoid actual memory allocation of 100MB+, let's mock/simulate, or since we are reading,
    # we can construct a dummy bytes object or generator. Let's send a stream or bytes.
    # Actually, let's pass a bytes of size MAX_FILE_SIZE + 1.
    payload = b"0" * (MAX_FILE_SIZE + 1)
    response = client.post(
        "/compress",
        files={"file": ("large.jpg", payload, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
