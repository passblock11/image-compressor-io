from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    # File size validation without reading entire content into memory first
    file.file.seek(0, 2)
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
        # pyvips.Image.new_from_buffer is faster than Pillow for opening
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

    # Convert to RGB if it has an alpha channel (RGBA) or is a palette image
    # pyvips handles this efficiently with flatten
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    MAX_WIDTH = 1600

    # Resize using pyvips thumbnail which is extremely fast as it integrates loading and shrinking
    if img.width > MAX_WIDTH:
        # We can use thumbnail_buffer directly if we hadn't already loaded it,
        # but since we need it for validation/conversion, we use thumbnail on the image object.
        img = img.thumbnail_image(MAX_WIDTH)

    # Compress image to JPEG buffer
    # quality=80, interlace=True (progressive), strip=True (remove metadata)
    output_buffer = img.jpegsave_buffer(
        Q=80,
        interlace=True,
        strip=True
    )

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
