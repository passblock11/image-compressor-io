import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

try:
    import pyvips
    PYVIPS_AVAILABLE = True
except Exception:  # noqa: BLE001
    PYVIPS_AVAILABLE = False
    from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Read uploaded file
        image_bytes = file.file.read()

        # File size validation
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

        MAX_WIDTH = 1600

        if PYVIPS_AVAILABLE:
            # High-performance pyvips pipeline
            img = pyvips.Image.new_from_buffer(image_bytes, "")

            if img.width > MAX_WIDTH:
                img = img.thumbnail_image(MAX_WIDTH, height=10000000)

            if img.interpretation not in ("cmyk", "scmyk"):
                has_a = False
                if hasattr(img, "hasalpha") and callable(img.hasalpha):
                    has_a = img.hasalpha()
                elif hasattr(img, "has_alpha"):
                    has_a = img.has_alpha
                else:
                    has_a = img.bands in (2, 4)

                if has_a:
                    img = img.colourspace("srgb").flatten(background=[255, 255, 255])

            output_bytes = img.jpegsave_buffer(
                Q=80,
                optimize_coding=True,
                interlace=True
            )
        else:
            # Optimized Pillow fallback pipeline
            img = Image.open(io.BytesIO(image_bytes))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            width, height = img.size
            if width > MAX_WIDTH:
                new_height = int(height * (MAX_WIDTH / width))
                img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

            output = io.BytesIO()
            img.save(
                output,
                format="JPEG",
                quality=80,
                optimize=True,
                progressive=True,
                subsampling=2
            )
            output_bytes = output.getvalue()

    except HTTPException:
        raise

    except Exception as e:  # noqa: BLE001
        if not PYVIPS_AVAILABLE and isinstance(e, UnidentifiedImageError):
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        if PYVIPS_AVAILABLE and isinstance(e, pyvips.Error):
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
