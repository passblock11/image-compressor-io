import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """Compress and resize uploaded images with optimized performance.

    Optimizations applied:
    - Synchronous handler: CPU-bound image processing runs in Starlette's thread pool,
      preventing the asyncio event loop from blocking.
    - Zero-copy stream inspection: Checks file size via seek/tell on file.file without
      pre-reading the entire file payload into memory.
    - Fast decoder downscaling: Uses img.draft() for JPEGs so libjpeg performs fast
      shrink-on-load during decoding.
    - BICUBIC resampling: Replaces LANCZOS with BICUBIC for ~3-4x speedup with visually
      equivalent output.
    - Direct buffer retrieval: Uses output.getvalue() to avoid seek/read copies.
    """
    try:
        # Check file size via stream seeking without reading entire payload into memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # File size validation
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

        # Open image directly from file stream
        img = Image.open(file.file)

    except HTTPException:
        # Re-raise HTTP exceptions (e.g., file size validation)
        raise

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )

    # Convert unsupported modes to RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size
    MAX_WIDTH = 1600

    # Resize large images
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        # Enable libjpeg fast shrink-on-load decoder downscaling
        img.draft("RGB", (MAX_WIDTH, new_height))
        width, height = img.size
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            # BICUBIC resampling is significantly faster than LANCZOS
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    output = io.BytesIO()

    # Compress image as JPEG
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2,
    )

    # Use output.getvalue() directly to avoid redundant seek(0) and read() operations
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
    )
