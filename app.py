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
    # Validate file size via stream position first
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

        image_bytes = file.file.read()

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Pyvips high-performance image processing
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Check for transparency/alpha channel
        has_alpha = False
        if hasattr(img, "has_alpha"):
            has_alpha = bool(img.has_alpha)
        elif hasattr(img, "hasalpha"):
            has_alpha = bool(img.hasalpha() if callable(img.hasalpha) else img.hasalpha)
        else:
            has_alpha = img.bands in (2, 4)

        if img.interpretation in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")
        elif has_alpha:
            img = img.colourspace("srgb").flatten(background=[255, 255, 255])

        MAX_WIDTH = 1600

        # Resize large images
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Compress and generate JPEG output buffer
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_bytes,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise explicit HTTP exceptions (e.g. 413, 400)
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
