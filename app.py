import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

# Try importing pyvips for fast libvips C-level image processing
try:
    import pyvips
    HAS_PYVIPS = True
except Exception:  # noqa: BLE001
    HAS_PYVIPS = False

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


# PERFORMANCE OPTIMIZATION: Using synchronous `def` instead of `async def` allows FastAPI
# to run this CPU-bound image processing task in Starlette's worker thread pool, preventing
# the main asyncio event loop from being blocked by heavy decoding/encoding work.
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # PERFORMANCE OPTIMIZATION: Check file size directly via seek/tell to avoid
        # loading the entire file into memory before size validation.
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

    except HTTPException:
        # Re-raise HTTP exceptions to avoid catching them as general exceptions
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # PERFORMANCE OPTIMIZATION: Fast path using pyvips (libvips) streaming pipeline
    if HAS_PYVIPS:
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")

            # Downscale only if width > MAX_WIDTH preserving aspect ratio
            if img.width > MAX_WIDTH:
                img = img.thumbnail_image(MAX_WIDTH, height=1000000)

            # Convert CMYK and non-sRGB images to sRGB
            img = img.colourspace("srgb")

            # Check for alpha channel across different pyvips versions/formats
            has_alpha = False
            if hasattr(img, "has_alpha"):
                has_alpha = bool(img.has_alpha)
            elif hasattr(img, "hasalpha"):
                has_alpha = bool(img.hasalpha() if callable(img.hasalpha) else img.hasalpha)
            else:
                has_alpha = img.bands in (2, 4)

            # Flatten alpha channel onto a white background
            if has_alpha:
                img = img.flatten(background=[255, 255, 255])

            # Export compressed JPEG buffer with Huffman table optimization and progressive loading
            output_bytes = img.jpegsave_buffer(
                Q=80,
                optimize_coding=True,
                interlace=True,
                subsample_mode="on"
            )

            return Response(
                content=output_bytes,
                media_type="image/jpeg"
            )

        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        except Exception:  # noqa: BLE001, S110
            # Fallback to Pillow pipeline below if pyvips processing fails
            pass

    # Fallback Pillow pipeline (also optimized with draft mode and BICUBIC resampling)
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # PERFORMANCE OPTIMIZATION: Use JPEG draft mode for libjpeg shrink-on-load speedup
        width, height = img.size
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            if img.format == "JPEG":
                img.draft("RGB", (MAX_WIDTH, new_height))

        # Convert non-RGB modes (RGBA, P, LA, CMYK, etc.) to RGB
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode in ("RGBA", "LA"):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img.convert("RGBA"))
                img = background
            else:
                img = img.convert("RGB")

        width, height = img.size
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            # PERFORMANCE OPTIMIZATION: BICUBIC resampling is significantly faster than LANCZOS
            # while offering equivalent visual quality in compressed JPEG outputs.
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

        output = io.BytesIO()

        img.save(
            output,
            format="JPEG",
            quality=80,
            optimize=True,
            progressive=True,
            subsampling=2
        )

        return Response(
            content=output.getvalue(),
            media_type="image/jpeg"
        )

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
