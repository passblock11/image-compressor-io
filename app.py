import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    try:
        # Optimized file size validation without reading entire file into memory first
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

        try:
            # Load image from buffer
            # We use new_from_buffer initially to check dimensions
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # Resize large images using shrink-on-load for performance
        if img.width > MAX_WIDTH:
            # height is set to a very large value to ensure width is the constraint
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle alpha channels (transparency) by flattening to white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress image to JPEG buffer
        # optimize_coding=True corresponds to optimize=True in Pillow
        # interlace=True corresponds to progressive=True in Pillow
        # strip=True removes metadata (EXIF, etc.) to reduce size further
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

    except HTTPException:
        # Re-raise HTTPExceptions to avoid them being caught by the generic Exception block
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
