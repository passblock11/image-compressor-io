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


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Validate file size without reading full file if too large
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
        # Open image lazily to inspect dimensions
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Resize large images using shrink-on-load
        if img.width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle alpha channels and non-sRGB colourspaces
        has_alpha = False
        if hasattr(img, "has_alpha"):
            has_alpha = img.has_alpha
        elif hasattr(img, "hasalpha"):
            has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
        else:
            has_alpha = img.bands in (2, 4)

        if has_alpha:
            img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])
        elif img.interpretation not in ("srgb", "b-w"):
            img = img.colourspace("srgb")

        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except HTTPException:
        raise
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
        content=output_bytes,
        media_type="image/jpeg"
    )
