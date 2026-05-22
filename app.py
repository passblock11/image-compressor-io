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
    Compress an uploaded image.
    Uses pyvips for high-performance image processing.
    """
    try:
        # Read uploaded file
        image_bytes = file.file.read()

        # File size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Use pyvips to load and resize in one step for better performance.
        # thumbnail_buffer is much faster than loading the full image and resizing.
        # size='down' ensures we only shrink images, never upscale.
        # height is set to a very large value to allow width-based constraint.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

    except pyvips.Error:
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

    # Handle transparency: if image has an alpha channel, flatten it onto a white background.
    # This maintains functional parity with the previous Pillow implementation.
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Compress image to JPEG.
    # Q=80: Quality level.
    # optimize_coding=True: Compute optimal Huffman coding tables.
    # interlace=True: Generate a progressive JPEG.
    output_buffer = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
