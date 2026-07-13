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
def compress(file: UploadFile = File(...)):
    try:
        # Efficient file size validation using seek/tell
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # read uploaded file
        image_bytes = file.file.read()

        # try opening image
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Upload failed")

    MAX_WIDTH = 1600

    # resize large images using shrink-on-load optimization if possible
    if img.width > MAX_WIDTH:
        # thumbnail_buffer is much faster as it performs shrink-on-load
        img = pyvips.Image.thumbnail_buffer(
            image_bytes, MAX_WIDTH, height=10000000  # Large height to preserve aspect ratio
        )

    # Convert to sRGB color space for consistency
    img = img.colourspace("srgb")

    # If image has alpha, flatten it onto a white background for JPEG
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # compress image
    # optimize_coding=True is equivalent to optimize=True in Pillow
    # interlace=True is equivalent to progressive=True in Pillow
    output_buffer = img.jpegsave_buffer(
        Q=80, optimize_coding=True, interlace=True, strip=True
    )

    return Response(content=output_buffer, media_type="image/jpeg")