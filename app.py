import io
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Validate file size efficiently without loading whole file into memory first if huge
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file",
        )

    # Read uploaded file content
    image_bytes = file.file.read()

    # Process image with pyvips for optimal speed and low memory usage
    try:
        img = pyvips.Image.new_from_buffer(image_bytes, "")
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )

    MAX_WIDTH = 1600

    # Resize large images while keeping aspect ratio
    if img.width > MAX_WIDTH:
        img = img.thumbnail_image(MAX_WIDTH, height=10000000)

    # Convert/flatten transparent layers to RGB with a white background
    if img.interpretation not in ("cmyk", "scmyk") and (
        hasattr(img, "hasalpha") and img.hasalpha()
    ):
        img = img.colourspace("srgb")
        img = img.flatten(background=[255, 255, 255])

    # Save image as optimized JPEG
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True,
        strip=True,
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg",
    )
