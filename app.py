import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

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


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # 1. Fast file size validation without unnecessary memory duplication
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

    # 2. Fast path: High-performance C-based image processing using pyvips/libvips
    # Def endpoint allows FastAPI to run CPU-bound libvips operations on thread pool
    if HAS_PYVIPS:
        try:
            vips_img = pyvips.Image.new_from_buffer(image_bytes, "")

            if vips_img.interpretation in ("cmyk", "scmyk"):
                vips_img = vips_img.colourspace("srgb")

            has_alpha = False
            if hasattr(vips_img, "has_alpha"):
                has_alpha = bool(vips_img.has_alpha)
            elif hasattr(vips_img, "hasalpha"):
                has_alpha = bool(
                    vips_img.hasalpha()
                    if callable(vips_img.hasalpha)
                    else vips_img.hasalpha
                )
            else:
                has_alpha = vips_img.bands in (2, 4)

            if has_alpha:
                vips_img = vips_img.colourspace("srgb")
                vips_img = vips_img.flatten(background=[255, 255, 255])

            if vips_img.width > MAX_WIDTH:
                vips_img = vips_img.thumbnail_image(MAX_WIDTH, height=10000000)

            output_bytes = vips_img.jpegsave_buffer(
                Q=80,
                optimize_coding=True,
                interlace=True,
                subsample_mode="on"
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

    # 3. Fallback path: Pillow engine
    try:
        img = Image.open(io.BytesIO(image_bytes))
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

    if img.mode != "RGB":
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

    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
