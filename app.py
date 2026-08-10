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
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Efficient file size validation without reading entire payload into memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        image_bytes = file.file.read()

        try:
            # Lazily load image metadata
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # High performance resizing using shrink-on-load thumbnail_buffer
        if img.width > 1600:
            img = pyvips.Image.thumbnail_buffer(image_bytes, 1600, height=10000000)

        # Determine if image has an alpha channel
        has_alpha = False
        if hasattr(img, 'has_alpha'):
            has_alpha = img.has_alpha
        elif hasattr(img, 'hasalpha'):
            if callable(img.hasalpha):
                has_alpha = img.hasalpha()
            else:
                has_alpha = img.hasalpha
        else:
            has_alpha = (img.bands in (2, 4))

        if has_alpha:
            img = img.flatten(background=[255, 255, 255])

        # Convert to sRGB for consistent output color profiles
        img = img.colourspace("srgb")

        # Compress to JPEG with high-performance settings
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

    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
