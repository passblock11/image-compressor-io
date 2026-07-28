import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Compresses an uploaded image file using the high-performance pyvips library.
    - Synchronously handles file size checks to avoid reading large files completely.
    - Performs lazy loading with new_from_buffer first to inspect properties.
    - Applies shrink-on-load via thumbnail_buffer if width is > 1600.
    - Flattens transparent/alpha bands to white background.
    - Standardizes output color space to sRGB.
    - Saves as progressive JPEG with Huffman optimization.
    """
    try:
        # Determine the file size efficiently without fully buffering it first
        try:
            file.file.seek(0, io.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)
        except (OSError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Upload failed"
            )

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

        try:
            image_bytes = file.file.read()
        except (OSError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Upload failed"
            )

        # Open image lazily with new_from_buffer to inspect its properties
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        width = img.width
        MAX_WIDTH = 1600

        # Resize large images using thumbnail_buffer for shrink-on-load optimization
        if width > MAX_WIDTH:
            try:
                img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)
            except pyvips.Error:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file or processing error"
                )

        # Flatten images with alpha channels (like RGBA or LA) to white background
        # since we are outputting to JPEG format which doesn't support transparency
        if img.hasalpha():
            try:
                img = img.flatten(background=[255, 255, 255])
            except pyvips.Error:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file or processing error"
                )

        # Convert to sRGB colourspace to ensure consistent JPEG colors
        try:
            img = img.colourspace("srgb")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file or processing error"
            )

        # Save/compress image to progressive JPEG bytes
        try:
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

    except HTTPException:
        # Re-raise HTTPExceptions to prevent them from being swallowed
        raise
    except Exception as e:
        # Catch other unexpected exceptions
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        ) from e

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
