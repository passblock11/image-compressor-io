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
        # Check file size efficiently before reading full buffer
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

        image_bytes = file.file.read()

        # Load image via pyvips for high-performance processing
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Downscale image if width exceeds MAX_WIDTH (1600)
        # thumbnail_image preserves aspect ratio and utilizes shrink-on-load speedups
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Cross-version safe check for alpha channel
        has_alpha = getattr(img, "has_alpha", None)
        if callable(has_alpha):
            has_alpha = has_alpha()
        elif has_alpha is None:
            has_alpha = getattr(img, "hasalpha", None)
            if callable(has_alpha):
                has_alpha = has_alpha()
            elif has_alpha is None:
                has_alpha = img.bands in (2, 4)

        # Handle alpha transparency and color space conversion
        if has_alpha:
            if img.interpretation not in ("cmyk", "scmyk"):
                img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])
        elif img.interpretation in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")

        # Save to JPEG buffer with progressive encoding, stripping EXIF/metadata, and Huffman optimization
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

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
