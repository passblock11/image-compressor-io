import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

try:
    import pyvips

    HAS_PYVIPS = True
except (ImportError, OSError):
    HAS_PYVIPS = False

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """Compresses uploaded image using pyvips (or Pillow fallback) with fast C-level downscaling,
    progressive JPEG encoding, and Starlette threadpool execution.
    """
    try:
        # Performance Optimization: O(1) file size check using stream seek without buffering payload into RAM first
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

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

        if HAS_PYVIPS:
            image_bytes = file.file.read()

            # Performance Optimization: pyvips uses libvips C pipeline for fast lazy decoding
            vimg = pyvips.Image.new_from_buffer(image_bytes, "")

            # Convert CMYK images to sRGB
            if vimg.interpretation in ("cmyk", "scmyk"):
                vimg = vimg.colourspace("srgb")

            # Determine alpha channel presence safely
            has_alpha = False
            if hasattr(vimg, "has_alpha"):
                has_alpha = (
                    vimg.has_alpha
                    if isinstance(vimg.has_alpha, bool)
                    else bool(vimg.has_alpha)
                )
            elif hasattr(vimg, "hasalpha"):
                has_alpha = (
                    vimg.hasalpha()
                    if callable(vimg.hasalpha)
                    else bool(vimg.hasalpha)
                )
            else:
                has_alpha = vimg.bands in (2, 4)

            # Flatten transparent layers over white background
            if has_alpha and vimg.interpretation not in ("cmyk", "scmyk"):
                vimg = vimg.colourspace("srgb").flatten(
                    background=[255, 255, 255]
                )

            # Performance Optimization: Fast libvips shrink-on-load downscaling
            if vimg.width > MAX_WIDTH:
                vimg = vimg.thumbnail_image(MAX_WIDTH, height=10000000)

            # Export progressive JPEG buffer
            output_bytes = vimg.jpegsave_buffer(
                Q=80, optimize_coding=True, interlace=True
            )

        else:
            try:
                img = Image.open(file.file)
            except UnidentifiedImageError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file",
                )

            # Convert unsupported modes
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            width, height = img.size

            # Performance Optimization: BICUBIC resampling for fast downscaling
            if width > MAX_WIDTH:
                new_height = int(height * (MAX_WIDTH / width))
                img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

            output = io.BytesIO()

            img.save(
                output,
                format="JPEG",
                quality=80,
                optimize=True,
                progressive=True,
                subsampling=2,
            )

            output_bytes = output.getvalue()

        return Response(content=output_bytes, media_type="image/jpeg")

    except HTTPException:
        # Prevent generic except block from swallowing explicit HTTP exceptions (e.g., 413 or 400 Empty file)
        raise

    except Exception as err:  # noqa: BLE001
        if HAS_PYVIPS and isinstance(err, pyvips.Error):
            raise HTTPException(
                status_code=400,
                detail="Invalid image file",
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )
