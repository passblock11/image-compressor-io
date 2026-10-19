import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


def _has_alpha_channel(img: pyvips.Image) -> bool:
    """Helper to detect if pyvips image has an alpha channel across pyvips versions."""
    if hasattr(img, "has_alpha"):
        return img.has_alpha
    if hasattr(img, "hasalpha"):
        val = img.hasalpha
        return val() if callable(val) else bool(val)
    return img.bands in (2, 4) and img.interpretation not in ("cmyk", "scmyk")


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Fast file size validation without reading payload entirely into memory first
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

        # Open image lazily via pyvips buffer
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Handle color spaces and alpha transparency safely
        if img.interpretation not in ("cmyk", "scmyk") and _has_alpha_channel(img):
            img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])
        elif img.interpretation in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")

        # Resize image preserving aspect ratio if width exceeds MAX_WIDTH
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Fast C-based JPEG compression with progressive interlace
        compressed_bytes = img.jpegsave_buffer(
            Q=80,
            interlace=True,
            optimize_coding=True,
        )

        return Response(
            content=compressed_bytes,
            media_type="image/jpeg",
        )

    except HTTPException:
        raise
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )
