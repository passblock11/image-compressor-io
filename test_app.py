import io
import time

from fastapi.testclient import TestClient
from PIL import Image

from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Image compression API running"}


def test_compress_large_jpeg():
    # Create image wider than MAX_WIDTH (1600)
    img = Image.new("RGB", (3000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("test.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 1600
    assert abs(out_img.size[1] - 1067) <= 1


def test_compress_small_jpeg():
    # Create image smaller than MAX_WIDTH
    img = Image.new("RGB", (800, 600), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("small.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.size[0] == 800
    assert out_img.size[1] == 600


def test_compress_rgba_png():
    # PNG with alpha channel
    img = Image.new("RGBA", (2000, 1500), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    response = client.post(
        "/compress",
        files={"file": ("transparent.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 1600


def test_compress_cmyk_jpeg():
    # CMYK JPEG
    img = Image.new("CMYK", (2000, 1500), color=(100, 50, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/compress",
        files={"file": ("cmyk.jpg", buf.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200

    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.mode == "RGB"
    assert out_img.size[0] == 1600


def test_empty_file():
    response = client.post(
        "/compress",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty file"


def test_invalid_file():
    response = client.post(
        "/compress",
        files={"file": ("bad.jpg", b"invalid data", "image/jpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image file"


def test_file_too_large():
    oversized = b"0" * (100 * 1024 * 1024 + 1)
    response = client.post(
        "/compress",
        files={"file": ("huge.jpg", oversized, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]


def test_benchmark_performance():
    # Measure endpoint response time for a 4000x3000 image
    img = Image.new("RGB", (4000, 3000), color="purple")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        response = client.post(
            "/compress",
            files={"file": ("benchmark.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 200
        times.append(time.perf_counter() - t0)

    avg_ms = (sum(times) / len(times)) * 1000
    print(f"\n[BENCHMARK] Average compression latency (4000x3000 -> 1600 width): {avg_ms:.2f} ms")
