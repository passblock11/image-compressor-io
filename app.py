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
    # Fast O(1) file size validation using stream seek/tell without reading full buffer into RAM
    try:
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        ) from e

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

        # Load image via pyvips (fast C library)
        vimg = pyvips.Image.new_from_buffer(image_bytes, "")

        # Convert CMYK colourspace to sRGB
        if vimg.interpretation in ("cmyk", "scmyk"):
            vimg = vimg.colourspace("srgb")

        # Detect alpha channel (RGBA, LA, etc.)
        has_alpha = False
        if hasattr(vimg, "hasalpha"):
            has_alpha = vimg.hasalpha() if callable(vimg.hasalpha) else vimg.hasalpha
        elif hasattr(vimg, "has_alpha"):
            has_alpha = vimg.has_alpha() if callable(vimg.has_alpha) else vimg.has_alpha
        else:
            has_alpha = vimg.bands in (2, 4) and vimg.interpretation not in ("cmyk", "scmyk")

        # Flatten alpha channel onto white background after ensuring sRGB colourspace
        if has_alpha:
            vimg = vimg.colourspace("srgb")
            vimg = vimg.flatten(background=[255, 255, 255])

        # Fast shrink-on-load downscaling if width exceeds MAX_WIDTH
        if vimg.width > MAX_WIDTH:
            vimg = vimg.thumbnail_image(MAX_WIDTH, height=10000000)

        # High-performance progressive JPEG buffer export
        compressed_bytes = vimg.jpegsave_buffer(Q=80, optimize_coding=True, interlace=True)

        return Response(
            content=compressed_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise explicit HTTP exceptions (e.g. 413 File too large, 400 Empty file)
        raise

    except pyvips.Error as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        ) from e
