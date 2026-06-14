from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # file size validation without reading entire file into memory first
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

    try:
        image_bytes = file.file.read()

        # Check if we need to resize
        # We use new_from_buffer for metadata only first, then thumbnail for actual work
        # to avoid redundant work if image is already small.
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        if img.width > MAX_WIDTH:
            # pyvips.Image.thumbnail_buffer is highly optimized for shrink-on-load
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # convert to RGB if it has alpha or is palletized
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # compress image to JPEG buffer
        # interlace=True makes it progressive
        # strip=True removes metadata (EXIF, etc.)
        # optimize_coding=True performs huffman optimization
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

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

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
