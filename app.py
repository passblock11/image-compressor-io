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
        # Check file size without reading full content into memory
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

        # Load and resize using pyvips for maximum performance.
        # thumbnail_buffer is highly optimized as it resizes during the loading process.
        # size='down' ensures we only shrink images and never upscale.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10_000_000,
            size='down'
        )

        # Handle transparency by flattening onto a background (defaults to black for JPEG)
        if img.hasalpha():
            img = img.flatten()

        # Export to optimized JPEG
        # Using Q=80, optimize_coding=True and interlace=True for best balance of speed and size.
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise FastAPIs HTTPExceptions
        raise
    except pyvips.Error as e:
        error_msg = str(e)
        if "not in a known format" in error_msg or "not a known format" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
