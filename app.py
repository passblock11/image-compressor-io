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
    # Using synchronous def to allow FastAPI to run this CPU-bound task in a thread pool.
    # read uploaded file
    image_bytes = file.file.read()

    # file size validation
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

    try:
        # try opening image to check if it is valid and get its width
        img = pyvips.Image.new_from_buffer(image_bytes, "")
        width = img.width

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

    # Resize large images using thumbnail_buffer for "shrink-on-load" optimization.
    # If no resizing is needed, we continue with the already opened 'img'.
    if width > MAX_WIDTH:
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

    # Convert to RGB (flatten alpha channel if present) to maintain parity with original Pillow logic.
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Compress image to JPEG format in memory.
    # interlace=True enables progressive JPEG.
    # optimize_coding=True performs Huffman table optimization.
    # strip=True removes metadata (EXIF, etc.) to further reduce size.
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