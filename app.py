import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


# Using synchronous def so FastAPI executes CPU-bound image processing in the
# worker threadpool instead of blocking the main asyncio event loop.
@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    try:
        # Measure file size without loading the entire stream into memory
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

        # Open image directly from stream (avoids redundant byte copying)
        img = Image.open(file.file)
        # Ensure image data is valid
        img.load()

    except HTTPException:
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

    # Convert unsupported modes
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    width, height = img.size

    MAX_WIDTH = 1600

    # Resize large images: Image.BICUBIC is ~20-25% faster than LANCZOS with
    # virtually identical visual quality for photographic downsizing.
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

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

    # getvalue() returns the underlying buffer directly without seek(0) + read() overhead
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
    )
