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

    try:
        # Check file size in O(1) time without loading entire file payload into RAM
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

        # Open image directly from file stream
        img = Image.open(file.file)

        MAX_WIDTH = 1600
        width, height = img.size

        # Fast draft downscaling for JPEGs during decode phase
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            if img.format == "JPEG":
                img.draft("RGB", (MAX_WIDTH, new_height))
                width, height = img.size

        # Convert non-RGB/L image modes (RGBA, P, LA, CMYK) to RGB
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Resize if width still exceeds MAX_WIDTH using fast BICUBIC filter
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    except HTTPException:
        # Re-raise HTTP exceptions to preserve 413 and 400 status codes
        raise

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    output = io.BytesIO()

    # Compress image
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2
    )

    # Directly retrieve output buffer bytes without redundant seeking and reading
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
