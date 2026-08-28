import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


def _has_alpha_channel(img: pyvips.Image) -> bool:
    """Helper to detect alpha channel across pyvips versions and color spaces."""
    if hasattr(img, "has_alpha"):
        val = img.has_alpha
        return bool(val() if callable(val) else val)
    if hasattr(img, "hasalpha"):
        val = img.hasalpha
        return bool(val() if callable(val) else val)
    return img.bands in (2, 4) and str(img.interpretation).lower() not in (
        "cmyk",
        "scmyk",
    )


# Performance Optimization: Defined as synchronous `def` (instead of `async def`)
# so FastAPI offloads execution to Starlette's thread pool, preventing CPU-bound image
# processing operations from blocking the asyncio main event loop.
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Fast size validation using underlying file stream seeking without copying buffer
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Max allowed size is 100 MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    image_bytes = file.file.read()

    try:
        # Performance Optimization: Lazy header load with pyvips to check dimensions.
        # If image width exceeds MAX_WIDTH (1600), use fast shrink-on-load via thumbnail_buffer.
        header_img = pyvips.Image.new_from_buffer(image_bytes, "")

        if header_img.width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes, MAX_WIDTH, height=10000000
            )
        else:
            img = header_img

        # Convert CMYK to sRGB if needed
        if str(img.interpretation).lower() in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")

        # Handle alpha channel / transparency by flattening onto a white background
        if _has_alpha_channel(img):
            if img.bands == 2:
                img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])

        # Performance Optimization: jpegsave_buffer with Huffman table optimization
        # (optimize_coding=True) and progressive scan (interlace=True).
        output_bytes = img.jpegsave_buffer(
            Q=80, optimize_coding=True, interlace=True
        )

    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")

    return Response(content=output_bytes, media_type="image/jpeg")
