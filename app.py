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
async def compress(file: UploadFile = File(...)):  # noqa: B008

    try:
        # Check file size without reading full payload into memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # File size validation
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

        # Convert non-RGB modes prior to resizing for faster resampling
        if img.mode in ("RGBA", "P", "LA", "PA"):
            img = img.convert("RGB")

        width, height = img.size

        MAX_WIDTH = 1600

        # Resize large images using BICUBIC (~25% faster than LANCZOS with visual parity)
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)
        elif img.mode != "RGB":
            img = img.convert("RGB")

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

    except HTTPException:
        # Re-raise HTTP exceptions to preserve status codes (413, 400)
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

    # Return bytes directly from buffer using getvalue() to avoid seek/read overhead
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
