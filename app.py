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
    # 1. Efficiently check file size without reading it into memory first
    try:
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    # 2. Read file contents into memory
    try:
        image_bytes = file.file.read()
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # 3. Process the image using pyvips
    try:
        # Lazily load image to check dimensions and format
        img = pyvips.Image.new_from_buffer(image_bytes, "")
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

    # 4. Resize large images using shrink-on-load (thumbnail_buffer)
    if img.width > MAX_WIDTH:
        try:
            # Performs shrink-on-load optimization; reads only pixels required for target size.
            # height is set extremely large to constrain width and maintain original aspect ratio.
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000
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

    # 5. Handle alpha transparency (flatten over white background)
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # 6. Ensure sRGB colourspace for consistent JPEG representation (e.g. from CMYK or Greyscale)
    img = img.colourspace("srgb")

    # 7. Compress the image to JPEG buffer
    try:
        compressed_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
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
        content=compressed_bytes,
        media_type="image/jpeg"
    )
