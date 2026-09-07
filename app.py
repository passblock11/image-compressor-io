import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Synchronous 'def' offloads CPU-bound PIL tasks to Starlette's worker thread pool,
    # preventing CPU operations from blocking the main asyncio event loop.
    try:
        # Fast file size validation in O(1) without reading full file bytes into memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB",
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Open image stream directly from file object to avoid unnecessary byte copying
        img = Image.open(file.file)

        width, height = img.size
        MAX_WIDTH = 1600

        # Fast resize for large images
        if width > MAX_WIDTH:
            target_height = int(height * (MAX_WIDTH / width))
            # Enable libjpeg shrink-on-load fast decoding for JPEGs
            if getattr(img, "format", None) == "JPEG":
                img.draft("RGB", (MAX_WIDTH, target_height))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Image.BICUBIC provides ~2x faster resampling than Image.LANCZOS
            img = img.resize((MAX_WIDTH, target_height), Image.BICUBIC)
        else:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

        output = io.BytesIO()

        # Compress image
        img.save(
            output,
            format="JPEG",
            quality=80,
            optimize=True,
            progressive=True,
            subsampling=2,
        )

        # Use getvalue() directly on BytesIO to eliminate seek/read overhead
        return Response(content=output.getvalue(), media_type="image/jpeg")

    except HTTPException:
        # Re-raise HTTPException to prevent masking 413 or 400 errors
        raise
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file")
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Upload failed")
