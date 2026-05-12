
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
        # Efficient file size validation without reading entire file into memory
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Load image using pyvips. thumbnail_buffer is very fast as it resizes during load.
        # We use a large height to effectively only constrain by width.
        MAX_WIDTH = 1600
        image_bytes = file.file.read()

        try:
            # size='down' ensures we don't upscale
            img = pyvips.Image.thumbnail_buffer(
                image_bytes, MAX_WIDTH, height=10000000, size='down'
            )
        except pyvips.Error as e:
            if "not a known format" in str(e).lower() or "not in a known format" in str(e).lower():
                raise HTTPException(status_code=400, detail="Invalid image file")
            raise

    except HTTPException:
        # Re-raise HTTPExceptions so they aren't caught by the general Exception block
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Upload failed")

    # Handle alpha channel: JPEG doesn't support transparency, so we flatten it
    if img.hasalpha():
        img = img.flatten()

    # Save to JPEG buffer with optimization and interlacing (progressive)
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
