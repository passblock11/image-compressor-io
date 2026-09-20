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
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


def _has_alpha_channel(img) -> bool:
    if hasattr(img, "has_alpha"):
        return bool(img.has_alpha)
    if hasattr(img, "hasalpha"):
        res = img.hasalpha
        return res() if callable(res) else bool(res)
    return img.bands in (2, 4)


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Compresses an uploaded image file.
    - Synchronous def offloads CPU-intensive image operations to Starlette worker threads.
    - Uses pyvips for fast stream-based thumbnailing and compression when available.
    - Preserves aspect ratio and resizes images wider than MAX_WIDTH (1600px).
    """
    # Fast file size validation
    file.file.seek(0, io.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Max allowed size is 100 MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    image_bytes = file.file.read()

    if PYVIPS_AVAILABLE:
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")

            # Resize if width exceeds MAX_WIDTH
            if img.width > MAX_WIDTH:
                img = img.thumbnail_image(MAX_WIDTH, height=10000000)

            # Ensure sRGB colourspace
            img = img.colourspace("srgb")

            # Flatten alpha layer if present
            if _has_alpha_channel(img):
                img = img.flatten(background=[255, 255, 255])

            # Export to JPEG buffer with Huffman table optimization & progressive encoding
            compressed_bytes = img.jpegsave_buffer(
                Q=80, optimize_coding=True, interlace=True
            )
            return Response(content=compressed_bytes, media_type="image/jpeg")
        except HTTPException:
            raise
        except pyvips.Error:
            raise HTTPException(status_code=400, detail="Invalid image file")
        except Exception:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Upload failed")
    else:
        # Fallback implementation with Pillow
        try:
            img = Image.open(io.BytesIO(image_bytes))
        except UnidentifiedImageError:
            raise HTTPException(status_code=400, detail="Invalid image file")
        except HTTPException:
            raise
        except Exception:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="Upload failed")

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
            subsampling=2,
        )
        return Response(content=output.getvalue(), media_type="image/jpeg")
