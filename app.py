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
        # Check file size efficiently without buffering entire payload into memory
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

        image_bytes = file.file.read()

        # Try opening image
        img = Image.open(io.BytesIO(image_bytes))

        # Convert unsupported modes
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        orig_width, orig_height = img.size
        MAX_WIDTH = 1600

        # Resize large images using fast libjpeg draft scaling and BICUBIC resampling
        if orig_width > MAX_WIDTH:
            new_height = int(orig_height * (MAX_WIDTH / orig_width))
            # Enable libjpeg fast downscaling during decode if JPEG
            img.draft("RGB", (MAX_WIDTH, new_height))
            # Resize to exact target dimensions using BICUBIC resampling
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

    except HTTPException:
        # Re-raise HTTPExceptions (413, 400) directly to prevent masking
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

    # Use output.getvalue() directly to avoid unnecessary seek and read ops
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
    )
