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


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    """
    Compresses and resizes uploaded images.
    Optimized:
    - Synchronous def offloads CPU-bound work to worker thread pool
    - Efficient stream size validation without full byte array copying
    - JPEG draft mode (shrink-on-load) for fast decoding
    - Image.BICUBIC filter for fast downsampling
    - Direct bytes extraction via output.getvalue()
    """
    try:
        # Validate file size without reading full payload into a byte string
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

        # Open image stream directly
        img = Image.open(file.file)

        # Get initial size
        width, height = img.size

        # Leverage libjpeg shrink-on-load draft mode if image needs resizing
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            if img.format == "JPEG":
                img.draft("RGB", (MAX_WIDTH, new_height))
                width, height = img.size
                new_height = int(height * (MAX_WIDTH / width))

            # Convert unsupported color modes
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resample image using fast BICUBIC filter
            if width > MAX_WIDTH:
                img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)
        else:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

    except HTTPException:
        # Re-raise explicit HTTP exceptions (e.g. 413, 400)
        raise
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

    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
