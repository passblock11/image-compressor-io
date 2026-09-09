import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


def _has_alpha(img: pyvips.Image) -> bool:
    """Check if a pyvips Image instance has an alpha channel across pyvips versions."""
    if hasattr(img, "has_alpha"):
        val = img.has_alpha
        return bool(val() if callable(val) else val)
    if hasattr(img, "hasalpha"):
        val = img.hasalpha
        return bool(val() if callable(val) else val)
    return img.bands in (2, 4)


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Read uploaded file bytes
        image_bytes = file.file.read()

        # File size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Performance optimization: Use pyvips for fast C-based SIMD/multi-threaded decoding & resizing
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Flatten transparent alpha layers onto a solid white background
        if _has_alpha(img):
            img = img.colourspace("srgb").flatten(background=[255, 255, 255])
        elif img.interpretation not in ("srgb", "bw"):
            img = img.colourspace("srgb")

        # Fast resize for large images preserving aspect ratio
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH)

        # Compress to progressive JPEG with optimized Huffman tables
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode="on"
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
