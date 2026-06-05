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
    # Using synchronous 'def' for the endpoint allows FastAPI to run this CPU-bound
    # task in a separate thread from the thread pool, preventing event loop blockage.

    try:
        # Check file size before reading the whole content if possible
        # Fastapi UploadFile has a 'file' attribute which is a SpooledTemporaryFile
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

        image_bytes = file.file.read()

        # pyvips.Image.new_from_buffer is very efficient and lazy
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except pyvips.error.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Flatten images with alpha channel (like PNG/RGBA) to RGB with a white background
    # for parity with the original Pillow implementation.
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    MAX_WIDTH = 1600

    # resize large images using thumbnail_buffer for maximum performance
    # thumbnail_buffer is faster because it performs shrink-on-load if supported by the loader
    if img.width > MAX_WIDTH:
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)
        # thumbnail_buffer might not preserve alpha correctly if not handled,
        # but since we flatten before if we used img.width, we should be careful.
        # Actually, if we use thumbnail_buffer, we should flatten AFTER if needed.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

    # Compress to JPEG
    # subsample_mode='on' forces 4:2:0 subsampling, similar to Pillow's default.
    # Note: Memory suggests subsample_mode might not be supported in some environments,
    # but also suggests it IS supported in 8.15. We will use it if it works.
    try:
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
        )
    except pyvips.error.Error:
        # Fallback if subsample_mode is not supported
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
