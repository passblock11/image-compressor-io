from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Synchronous endpoint for CPU-bound image processing.
    FastAPI will run this in a thread pool, avoiding blocking the event loop.
    """
    try:
        # Validate file size without reading everything into memory
        file.file.seek(0, 2)  # seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # reset to start

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024*1024)} MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        # Open image directly from the stream to avoid redundant memory copies
        img = Image.open(file.file)

        # convert unsupported modes
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # Resize large images using thumbnail() and BICUBIC for speed/quality balance
        # thumbnail() is more efficient as it modifies the image in-place
        if img.width > MAX_WIDTH:
            img.thumbnail((MAX_WIDTH, img.height), Image.BICUBIC)

        output = io.BytesIO()

        # compress image
        img.save(
            output,
            format="JPEG",
            quality=80,
            optimize=True,
            progressive=True,
            subsampling=2
        )

        # Use getvalue() for direct access to the buffer
        return Response(
            content=output.getvalue(),
            media_type="image/jpeg"
        )

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
