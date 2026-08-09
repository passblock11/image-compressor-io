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
async def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Highly optimized image compression endpoint utilizing pyvips.
    Uses 'shrink-on-load' optimization and zero-copy buffering
    for maximum performance and extremely low memory footprint.
    """
    try:
        # Perform robust file size checking using file seek/tell
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

        # Read the uploaded file into memory
        image_bytes = await file.read()

        # Initialize pyvips image lazily from buffer
        img = pyvips.Image.new_from_buffer(image_bytes, "")

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

    MAX_WIDTH = 1600

    # Resize large images using shrink-on-load / thumbnailing
    if img.width > MAX_WIDTH:
        img = img.thumbnail_image(MAX_WIDTH, height=10000000)

    # Cross-version compatible check for alpha channel
    if hasattr(img, "has_alpha"):
        has_alpha = img.has_alpha
    elif hasattr(img, "hasalpha"):
        has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
    else:
        has_alpha = img.bands in (2, 4)

    # Flatten transparent images with white background for JPEG compatibility
    if has_alpha:
        img = img.flatten(background=[255, 255, 255])

    # Convert colourspace to srgb to ensure consistent RGB format
    img = img.colourspace("srgb")

    # Highly optimized JPEG compression directly to buffer
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True,
        strip=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
