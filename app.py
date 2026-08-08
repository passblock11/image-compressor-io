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
    try:
        # file size validation using seek and tell
        file.file.seek(0, io.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        image_bytes = file.file.read()

        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # Convert transparency/alpha channels
        # hasalpha returns 1 (True) or 0 (False) or might be callable depending on pyvips version
        has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
        if has_alpha:
            img = img.flatten(background=[255, 255, 255])

        # Ensure consistent color space (e.g. CMYK to sRGB)
        img = img.colourspace("srgb")

        width = img.width
        MAX_WIDTH = 1600

        # resize large images using fast thumbnail_image method
        if width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # compress image to JPEG
        # optimize_coding=True performs Huffman table optimization
        # interlace=True enables progressive loading
        # strip=True removes metadata/EXIF for efficiency
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
