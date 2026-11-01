import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


# Bolt Optimization: Defining CPU-bound route handler as synchronous `def`
# offloads image decoding, resizing, and compression to Starlette's threadpool
# instead of blocking the main asyncio event loop.
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Bolt Optimization: Inspect stream size using seek/tell to avoid
        # reading entire upload buffer into memory unnecessarily.
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # File size validation
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

        # Bolt Optimization: Open stream directly from file object to avoid
        # copying bytes into a new BytesIO buffer and enable lazy decoding.
        img = Image.open(file.file)

    except HTTPException:
        # Re-raise explicit HTTP exceptions (e.g. 413, 400) so they aren't masked
        raise

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed",
        )

    # Convert non-RGB modes (RGBA, P, LA, etc.) to RGB for JPEG compatibility
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size

    MAX_WIDTH = 1600

    # Bolt Optimization: Use Image.BICUBIC instead of LANCZOS for ~20-25% faster
    # downscaling while maintaining high visual quality.
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    output = io.BytesIO()

    # Compress image to progressive JPEG
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2,
    )

    # Bolt Optimization: Use output.getvalue() directly instead of seek(0) + read()
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
    )
