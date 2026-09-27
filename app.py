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
    # Validate file size directly via stream seeking without loading payload into memory
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

    try:
        # Pass file stream directly to Image.open for lazy header loading
        img = Image.open(file.file)
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

    # Convert unsupported modes
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size

    MAX_WIDTH = 1600

    # Fast JPEG draft downscaling during decode for large images
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        if img.format == "JPEG":
            img.draft("RGB", (MAX_WIDTH, new_height))
            width, height = img.size
            new_height = int(height * (MAX_WIDTH / width))

        if width > MAX_WIDTH:
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    output = io.BytesIO()

    # Compress image to JPEG
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2
    )

    # Use output.getvalue() to return bytes buffer directly without extra stream copies
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
