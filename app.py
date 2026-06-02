from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # file size validation without reading entire content into memory first
    file.file.seek(0, 2)
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

    try:
        # read uploaded file content
        image_bytes = file.file.read()

        # Check dimensions using new_from_buffer (header-only load if possible)
        # then decide whether to use thumbnail_buffer (shrink-on-load) or use as-is
        img_header = pyvips.Image.new_from_buffer(image_bytes, "")
        if img_header.width > MAX_WIDTH:
            # Use thumbnail_buffer for efficient shrink-on-load
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)
        else:
            img = img_header

    except pyvips.error.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # convert to RGB by flattening alpha channel if it exists
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # compress image to JPEG buffer
    # optimize_coding=True and interlace=True provide good compression/progressive load
    output_buffer = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_buffer, media_type="image/jpeg"
    )
