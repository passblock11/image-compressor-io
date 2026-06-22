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
    # Validate file size before reading into memory
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
        image_bytes = file.file.read()

        # Use pyvips for high-performance image processing
        # new_from_buffer is lazy and only reads metadata initially
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Optimize: use thumbnail_buffer for shrink-on-load if resizing is needed
        if img.width > MAX_WIDTH:
            # Setting a very large height ensures aspect ratio is preserved based on MAX_WIDTH
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # JPEG does not support alpha channels; flatten onto a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Save to JPEG buffer with optimizations
        # Q=80: quality level
        # optimize_coding=True: Huffman table optimization (matches Pillow's optimize=True)
        # interlace=True: Progressive JPEG (matches Pillow's progressive=True)
        # strip=True: Remove metadata to reduce file size
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
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
