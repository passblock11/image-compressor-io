import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def _has_alpha(img: pyvips.Image) -> bool:
    """Check if a pyvips image has an alpha channel in a cross-version compatible way."""
    if hasattr(img, "hasalpha"):
        res = img.hasalpha()
        return bool(res() if callable(res) else res)
    if hasattr(img, "has_alpha"):
        res = img.has_alpha
        return bool(res() if callable(res) else res)
    return img.bands in (2, 4) and getattr(img, "interpretation", None) not in ("cmyk", "scmyk")


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Fast in-memory size validation using stream seek/tell without reading full buffer
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )

    image_bytes = file.file.read()

    try:
        # pyvips open from buffer (lazy loading)
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # Resize if image width exceeds max width
        if img.width > MAX_WIDTH:
            # thumbnail_image on an existing lazy Image object is faster than thumbnail_buffer
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Handle alpha channel flattening for PNG/RGBA/LA formats
        if _has_alpha(img):
            img = img.colourspace("srgb").flatten(background=[255, 255, 255])
        elif getattr(img, "interpretation", None) == "cmyk":
            img = img.colourspace("srgb")

        # Save to JPEG buffer using pyvips
        # Q: quality (80), interlace: progressive (True), strip: remove metadata (True), optimize_coding: Huffman optimization (True)
        jpeg_data = img.jpegsave_buffer(
            Q=80,
            interlace=True,
            strip=True,
            optimize_coding=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=jpeg_data,
        media_type="image/jpeg"
    )
