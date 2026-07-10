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
    # Get file size without reading everything into memory at once
    try:
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
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Load image lazily to check dimensions
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600

        # Use thumbnail_buffer for efficient resize (shrink-on-load) if needed
        if img.width > MAX_WIDTH:
            # We use a very large height to ensure aspect ratio is maintained based on width
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Ensure sRGB color space
        img = img.colourspace("srgb")

        # Flatten alpha channel (RGBA/P -> RGB) with white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress to JPEG
        # optimize_coding=True is equivalent to Pillow's optimize=True (Huffman table optimization)
        # interlace=True is equivalent to Pillow's progressive=True
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Compression failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
