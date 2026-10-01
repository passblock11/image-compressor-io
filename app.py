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
    # Fast file size validation without unnecessary memory allocation
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

    try:
        image_bytes = file.file.read()

        # High-performance image loading via pyvips
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Resize image maintaining aspect ratio using fast libvips thumbnailing
        MAX_WIDTH = 1600
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Convert CMYK images to sRGB
        if img.interpretation in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")

        # Handle alpha / transparent channels by flattening onto a white background
        has_alpha = False
        if hasattr(img, "has_alpha"):
            has_alpha = bool(img.has_alpha)
        elif hasattr(img, "hasalpha"):
            has_alpha = bool(img.hasalpha() if callable(img.hasalpha) else img.hasalpha)
        else:
            has_alpha = img.bands in (2, 4)

        if has_alpha:
            if img.bands == 2:
                img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])

        # Save compressed progressive JPEG directly to bytes
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
