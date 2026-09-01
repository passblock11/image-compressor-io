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
    try:
        # Fast file size check using file pointer seeking without reading whole stream into memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB",
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Read uploaded file bytes
        image_bytes = file.file.read()

        # Load image via pyvips (fast C library lazy loading)
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Resize image if width exceeds MAX_WIDTH (1600)
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Handle alpha transparency / band conversion before saving to JPEG
        has_alpha = False
        if hasattr(img, "hasalpha"):
            has_alpha = bool(img.hasalpha())
        elif hasattr(img, "has_alpha"):
            has_alpha = bool(img.has_alpha)
        else:
            has_alpha = img.bands in (2, 4)

        if has_alpha and img.interpretation != "cmyk":
            if img.bands == 2:
                img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])

        # Save image as JPEG with pyvips (Q=80, Huffman table optimization, progressive, strip metadata)
        compressed_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True,
        )

        return Response(content=compressed_bytes, media_type="image/jpeg")

    except HTTPException:
        # Re-raise HTTP exceptions directly to preserve status code (e.g., 413 or 400)
        raise

    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")

    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")
