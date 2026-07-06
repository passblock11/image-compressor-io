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
    # file size validation using seek/tell to avoid reading large files into memory twice
    try:
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

        # read uploaded file
        image_bytes = file.file.read()

        # try opening image
        # Using new_from_buffer for metadata-only load initially
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except HTTPException:
        # Re-raise HTTPExceptions so they aren't swallowed by the generic Exception block
        raise
    except pyvips.error.Error:
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

    # resize large images using shrink-on-load optimization
    if img.width > MAX_WIDTH:
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

    # convert unsupported modes / handle transparency
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # ensure sRGB
    img = img.colourspace("srgb")

    # compress image to JPEG
    # optimize_coding=True is equivalent to Pillow's optimize=True
    # interlace=True is equivalent to Pillow's progressive=True
    # strip=True removes metadata for smaller file size
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
