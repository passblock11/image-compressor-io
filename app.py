from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # Efficiently check file size without reading everything into memory first
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
        # Read uploaded file
        image_bytes = file.file.read()

        # We use new_from_buffer first to check the width lazily.
        # This is faster than full decoding if we don't need to resize.
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        if img.width > MAX_WIDTH:
            # thumbnail_buffer is significantly faster as it performs shrink-on-load,
            # reading only the pixels required for the target size from the source.
            # We set height to a very large value to ensure we only constrain by width,
            # preserving the aspect ratio.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Handle transparency: flatten to white background if alpha channel is present.
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure sRGB output for consistent JPEG colors
        img = img.colourspace("srgb")

        # Compress to JPEG buffer with optimizations
        # Q: quality, optimize_coding: Huffman table optimization, interlace: progressive JPEG
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

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
