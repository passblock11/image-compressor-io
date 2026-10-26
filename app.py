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
    # Validate file size using stream position without reading full payload into memory
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

    try:
        # Pass stream directly to Image.open to exploit lazy loading
        img = Image.open(file.file)
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

    # Convert non-RGB modes (e.g. RGBA, P, CMYK, LA) to RGB for JPEG compatibility
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    MAX_WIDTH = 1600

    # Resize large images using BICUBIC resampling (~20-25% speedup vs LANCZOS)
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

    # Use getvalue() directly to avoid redundant stream re-seeking and reading
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg",
    )
