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
    # Performance optimization: Use synchronous def instead of async def to avoid
    # blocking the main asyncio event loop during CPU-intensive image compression.
    # FastAPI automatically runs synchronous path operations in Starlette's worker thread pool.
    try:
        # read uploaded file
        image_bytes = file.file.read()

        # file size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB",
            )

        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file",
            )

        # Performance optimization: Use pyvips with shrink-on-load via thumbnail_buffer.
        # This dramatically reduces memory allocation and CPU decode time compared to PIL,
        # shrinking directly during JPEG DCT decoding rather than decoding full resolution first.
        # size="down" prevents upscaling images whose width is <= MAX_WIDTH.
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10_000_000,
            size="down",
        )

        # Convert non-standard color spaces (e.g. CMYK) to sRGB
        if img.interpretation in ("cmyk", "scmyk"):
            img = img.colourspace("srgb")

        # Flatten transparent alpha channels (RGBA, LA) onto a solid white background
        if (
            (hasattr(img, "hasalpha") and img.hasalpha())
            or getattr(img, "has_alpha", False)
            or img.bands in (2, 4)
        ):
            img = img.colourspace("srgb")
            img = img.flatten(background=[255, 255, 255])

        # Export compressed progressive JPEG with 4:2:0 subsampling
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode="on",
        )

    except HTTPException:
        # Re-raise explicit HTTP exceptions so they are not masked
        raise

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg",
    )
