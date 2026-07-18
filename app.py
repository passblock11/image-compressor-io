from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import io
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # file size validation without reading entire file into memory first
    try:
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

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
        # read uploaded file bytes synchronously
        image_bytes = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Use pyvips to lazily load and inspect image metadata
        img = pyvips.Image.new_from_buffer(image_bytes, "")
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

    # Max allowed width
    MAX_WIDTH = 1600
    width = img.width

    try:
        # If width exceeds MAX_WIDTH, we downsize using pyvips.Image.thumbnail_buffer.
        # This performs "shrink-on-load" optimization if the underlying loader supports it,
        # which is extremely fast and memory efficient.
        if width > MAX_WIDTH:
            # We set a very large height so that only the width limits the resize operation,
            # preserving the aspect ratio behavior of the original Pillow implementation.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )

    try:
        # Handle transparency (flatten alpha channel to white)
        # In current environment, hasalpha() returns 1 (True) or 0 (False)
        if img.hasalpha():
            # pyvips.Image.flatten is completely safe for 2-band or 4-band images
            img = img.flatten(background=[255, 255, 255])

        # Ensure we are in srgb colorspace to guarantee consistent RGB output
        img = img.colourspace("srgb")

        # Compress image to JPEG format using optimal settings
        # Q=80, interlace=True (progressive JPEG), optimize_coding=True (Huffman optimization),
        # strip=True (strips EXIF, ICC profiles, etc. to match original behavior and reduce file size)
        compressed_bytes = img.jpegsave_buffer(
            Q=80,
            interlace=True,
            optimize_coding=True,
            strip=True
        )
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )

    return Response(
        content=compressed_bytes,
        media_type="image/jpeg"
    )