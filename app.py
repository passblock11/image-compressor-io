import io
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
async def compress(file: UploadFile = File(...)):  # noqa: B008

    # Performance Optimization: Determine upload size directly via file pointer seeking
    # without allocating/reading the full payload into Python memory first.
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    # file size validation
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
        # Performance Optimization: Pass file stream directly to Pillow
        # to exploit lazy-loading and avoid copying byte string buffers into memory.
        img = Image.open(file.file)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except HTTPException:
        # Re-raise HTTP exceptions to preserve correct error status codes and detail messages
        raise

    except Exception: # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # convert unsupported modes
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size

    MAX_WIDTH = 1600

    # resize large images
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

    output = io.BytesIO()

    # compress image
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2
    )

    # Performance Optimization: Use getvalue() directly to return byte buffer without seek(0) + read() overhead
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
