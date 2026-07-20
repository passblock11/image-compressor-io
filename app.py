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
    # file size validation without reading the whole file in memory
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
        image_bytes = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Check metadata lazily first using new_from_buffer
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

    MAX_WIDTH = 1600

    try:
        # Resize using pyvips.Image.thumbnail_buffer if width exceeds MAX_WIDTH
        if img.width > MAX_WIDTH:
            # We configure height to be extremely large (10000000) to ensure
            # pyvips constraints only the width to MAX_WIDTH, preserving aspect ratio.
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000
            )

        # Ensure color profile is standard sRGB
        img = img.colourspace("srgb")

        # Convert/Flatten alpha/transparency modes to RGB on a white background
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Compress and save to JPEG buffer with high-performance parameters:
        # - Q=80 (Quality level)
        # - optimize_coding=True (Huffman table optimization)
        # - interlace=True (Progressive JPEG rendering)
        # - strip=True (Strip all metadata/EXIF/ICC profiles for reduced file size)
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
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

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
