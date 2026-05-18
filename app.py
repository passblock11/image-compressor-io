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
    """
    Compresses an image using pyvips for high performance.
    Switching to synchronous 'def' allows FastAPI to use an external thread pool,
    avoiding event loop blockage during CPU-bound image processing.
    """
    try:
        # validate file size without reading full content into memory
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

        # read file content for pyvips
        image_bytes = file.file.read()

        # use thumbnail_buffer for fast resizing during loading
        # size='down' prevents upscaling
        # large height (10m) ensures we only constrain by width while preserving aspect ratio
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

        # handle transparency and modes (convert to RGB for JPEG)
        if img.hasalpha():
            img = img.flatten()

        # compress to JPEG buffer
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException as e:
        # re-raise known HTTP exceptions
        raise e

    except pyvips.Error as e:
        # map pyvips errors to meaningful responses
        err_msg = str(e).lower()
        if "not in a known format" in err_msg or "not a known format" in err_msg:
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
