from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


def has_alpha_channel(img: pyvips.Image) -> bool:
    if hasattr(img, "has_alpha"):
        if callable(img.has_alpha):
            return bool(img.has_alpha())
        return bool(img.has_alpha)
    if hasattr(img, "hasalpha"):
        if callable(img.hasalpha):
            return bool(img.hasalpha())
        return bool(img.hasalpha)
    return img.bands in (2, 4)


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Seek to the end to get file size efficiently without reading everything first
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # File size validation
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

        # Read the file contents as bytes
        image_bytes = file.file.read()

        try:
            # Load the image lazily using new_from_buffer
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    width = img.width

    MAX_WIDTH = 1600

    # Resize large images using thumbnail_image for maximum performance (shrink-on-load)
    if width > MAX_WIDTH:
        img = img.thumbnail_image(MAX_WIDTH, height=10000000)

    # Convert to sRGB color space FIRST to handle grayscale and alpha channel consistency safely
    img = img.colourspace("srgb")

    # Flatten transparent images (like PNG/RGBA/LA) onto a white background SECOND
    if has_alpha_channel(img):
        img = img.flatten(background=[255, 255, 255])

    try:
        # Compress and save to JPEG buffer with Huffman table optimization, progressive mode and stripped metadata
        compressed_bytes = img.jpegsave_buffer(
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

    return Response(
        content=compressed_bytes,
        media_type="image/jpeg"
    )
