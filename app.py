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
    """
    Compresses an uploaded image using pyvips for high performance.
    Resizes images to a max width of 1600px while preserving aspect ratio.
    Converts output to optimized, progressive JPEG.
    """
    try:
        # Efficiently check file size without reading everything into memory yet
        file.file.seek(0, io.SEEK_END)
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

        image_bytes = file.file.read()

        MAX_WIDTH = 1600

        # Load image lazily to check dimensions
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Use shrink-on-load (thumbnail_buffer) if resizing is needed
        # This is significantly faster than loading full image then resizing
        if img.width > MAX_WIDTH:
            # We set a very large height to ensure only width is the constraint
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Ensure consistent sRGB colorspace
        if img.interpretation != 'srgb':
            img = img.colourspace('srgb')

        # Flatten transparency against a white background for JPEG compatibility
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Save to JPEG buffer with optimizations
        # Q=80 matches original quality
        # optimize_coding=True performs Huffman table optimization
        # interlace=True creates progressive JPEGs
        # strip=True removes metadata (EXIF, ICC, etc.) to reduce size
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise HTTPExceptions (like file too large or empty)
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
