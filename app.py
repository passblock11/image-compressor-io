import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


# Using synchronous 'def' instead of 'async def' offloads CPU-bound image operations
# to Starlette's thread pool, preventing blocking of the main asyncio event loop.
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Efficiently read upload file bytes
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

        # Load image lazily using libvips without immediately decoding full pixel data
        img = pyvips.Image.new_from_buffer(image_bytes, "")

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

    # Convert color spaces if needed (e.g. CMYK or non-sRGB 4-band images)
    if img.interpretation not in ("srgb", "p") and img.bands == 4:
        img = img.colourspace("srgb")

    # Handle alpha channel (flatten RGBA / LA to RGB with white background)
    has_alpha = False
    if hasattr(img, "has_alpha"):
        has_alpha = img.has_alpha
    elif hasattr(img, "hasalpha"):
        has_alpha = img.hasalpha() if callable(img.hasalpha) else img.hasalpha
    else:
        has_alpha = img.bands in (2, 4)

    if has_alpha:
        img = img.flatten(background=[255, 255, 255])

    MAX_WIDTH = 1600

    # Fast resizing using thumbnail_image on the opened lazily-loaded image object
    if img.width > MAX_WIDTH:
        img = img.thumbnail_image(MAX_WIDTH, height=10000000)

    # Fast C-level JPEG compression with Huffman table optimization and progressive interlace
    compressed_output = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True,
        strip=True
    )

    return Response(
        content=compressed_output,
        media_type="image/jpeg"
    )
