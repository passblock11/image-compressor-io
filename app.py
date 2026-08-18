import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Compress and resize uploaded images.

    Performance optimizations:
    1. Uses `pyvips` instead of `Pillow` for C-level libvips execution (~4x faster throughput).
    2. Uses synchronous `def` endpoint so FastAPI executes this CPU-bound work in a threadpool,
       preventing event-loop blocking under high concurrence.
    3. Efficiently checks file size using stream seeking (`file.file.seek/tell`) without loading
       the full payload into memory first.
    4. Utilizes `pyvips.Image.thumbnail_buffer` for shrink-on-load optimization (reading only required
       pixels during decoding) when width > 1600.
    """
    try:
        # Get file size using file stream seeking to avoid redundant byte memory allocations
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        image_bytes = file.file.read()

        # Check metadata lazily
        vimg = pyvips.Image.new_from_buffer(image_bytes, "")

        # Shrink-on-load with pyvips if width exceeds MAX_WIDTH
        if vimg.width > MAX_WIDTH:
            vimg = pyvips.Image.thumbnail_buffer(
                image_bytes, MAX_WIDTH, height=10000000
            )

        # Convert CMYK images to sRGB
        if vimg.interpretation in ("cmyk", "scmyk"):
            vimg = vimg.colourspace("srgb")

        # Determine if image has alpha channel across pyvips versions
        has_alpha = False
        if hasattr(vimg, "has_alpha"):
            has_alpha = bool(vimg.has_alpha)
        elif hasattr(vimg, "hasalpha"):
            has_alpha = bool(
                vimg.hasalpha() if callable(vimg.hasalpha) else vimg.hasalpha
            )
        else:
            has_alpha = vimg.bands in (2, 4)

        if has_alpha:
            vimg = vimg.colourspace("srgb")
            vimg = vimg.flatten(background=[255, 255, 255])

        # Save to JPEG buffer with progressive encoding & Huffman table optimization
        output_bytes = vimg.jpegsave_buffer(
            Q=80, optimize_coding=True, interlace=True, strip=True
        )

    except HTTPException:
        raise
    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")

    return Response(content=output_bytes, media_type="image/jpeg")
