import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Fast file size check using file object seeking without reading whole payload
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file",
        )

    image_bytes = file.file.read()

    try:
        # Load image via pyvips for fast, low-memory C-level demand-driven execution
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Convert CMYK or 2-band (grayscale + alpha) images to sRGB
        if img.interpretation in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")
        if img.bands == 2:
            img = img.colourspace("srgb")

        # Flatten alpha transparency over a solid white background
        if img.bands in (2, 4):
            img = img.flatten(background=[255, 255, 255])

        MAX_WIDTH = 1600

        # High performance shrink-on-load / downscaling preserving aspect ratio
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Output progressive JPEG buffer with optimized Huffman coding
        output_bytes = img.jpegsave_buffer(
            Q=80, optimize_coding=True, interlace=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg",
    )
