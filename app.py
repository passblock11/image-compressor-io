import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


# Synchronous endpoint offloads CPU-bound image processing to Starlette thread pool,
# avoiding blocking the main asyncio event loop.
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Validate file size using stream seek/tell to avoid buffering entire file in memory
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

        # Pass stream directly to Image.open for lazy image header loading
        img = Image.open(file.file)

    except HTTPException:
        # Re-raise HTTPException to preserve 413 and 400 response status codes
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

    # Convert non-RGB modes (e.g. RGBA, P, LA) to RGB before saving as JPEG
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size

    # Resize large images using BICUBIC filter for faster resampling with equivalent visual quality
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    output = io.BytesIO()

    # Compress image as optimized progressive JPEG
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2,
    )

    # Direct buffer retrieval avoids redundant stream seek and read calls
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
    )
