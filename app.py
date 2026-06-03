from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # file size validation using stream
    try:
        file.file.seek(0, 2)
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

        # Load image from buffer
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except HTTPException:
        raise
    except Exception:
        # Fallback to general error as original implementation did for most cases
        raise HTTPException(
            status_code=400,
            detail="Invalid image file" if 'image_bytes' in locals() else "Upload failed"
        )

    MAX_WIDTH = 1600

    # Check if resizing is needed
    if img.width > MAX_WIDTH:
        # Use thumbnail_buffer for efficient resizing if we have the buffer
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

    # Handle transparency by flattening onto white background
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Compress to JPEG
    # Note: subsampling_mode is not supported in some libvips versions,
    # we'll use the default or standard parameters.
    # original used subsampling=2 which usually means 4:2:0 in Pillow
    # In pyvips jpegsave, Q=80 is similar.

    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
