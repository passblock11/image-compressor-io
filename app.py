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
        # Stream file size validation using seek/tell to avoid loading full byte string into RAM
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

        # Open image directly from file stream for lazy metadata loading and reduced memory footprint
        img = Image.open(file.file)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except HTTPException:
        # Re-raise HTTPException so 413 File Too Large and 400 Empty File status codes are preserved
        raise

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Convert non-RGB modes (RGBA, P, LA, CMYK, etc.) to RGB prior to JPEG export
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    MAX_WIDTH = 1600

    # Resize large images using BICUBIC filter for ~25-30% faster downscaling
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    output = io.BytesIO()

    # Compress image as JPEG
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2
    )

    # Return output.getvalue() directly to avoid redundant seek and read stream calls
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
