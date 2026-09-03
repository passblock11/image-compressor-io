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
    # Using sync def so FastAPI offloads CPU-bound libvips operations to worker threadpool
    try:
        image_bytes = file.file.read()

        # file size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Open image lazily with pyvips
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        # Resize large images using libvips fast shrink-on-load thumbnail (width constrained to MAX_WIDTH)
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH, height=10000000)

        # Convert non-sRGB/grayscale interpretation (e.g. CMYK, LAB) to sRGB first
        if img.interpretation not in ("srgb", "b-w"):
            img = img.colourspace("srgb")

        # Flatten alpha channel to a clean white background if present
        if img.hasalpha() or img.bands in (2, 4):
            if img.bands == 2:
                img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])

        # Save compressed JPEG buffer with Huffman coding optimization and progressive interlace
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
