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
    try:
        # Check file size without reading everything into memory first
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

        # Load image from memory
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # Handle transparency: flatten RGBA to RGB with white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Efficient resizing using thumbnail_buffer if width > MAX_WIDTH
        if img.width > MAX_WIDTH:
            # thumbnail_buffer is very fast as it performs shrink-on-load
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000, # Large height to maintain aspect ratio based on width
                size='down'
            )
            # Re-apply flattening if thumbnail_buffer returned alpha (unlikely for JPEG but good for safety)
            if img.hasalpha():
                img = img.flatten(background=[255, 255, 255])

        # Compress and save to buffer
        # interlace=True corresponds to progressive JPEG
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions to keep their status codes
        raise
    except Exception:
        # Log error in real scenarios
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
