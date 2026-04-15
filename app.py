from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    """
    Compresses an uploaded image.
    Uses synchronous 'def' so FastAPI runs it in a threadpool,
    avoiding event loop blocking during heavy CPU bound image processing.
    """
    try:
        # file size validation without reading entire file into RAM
        file.file.seek(0, 2)
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

        # try opening image directly from file stream
        img = Image.open(file.file)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise HTTP exceptions to avoid being caught by generic Exception block
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Convert modes with alpha channel to RGB BEFORE resizing.
    # Resizing 3 channels is ~25% faster than resizing 4 (RGBA).
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGB")

    width, height = img.size
    MAX_WIDTH = 1600

    # resize large images
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        # Use BICUBIC for better balance of speed and quality than LANCZOS
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    # ensure final output is RGB (e.g. for CMYK or L images)
    if img.mode != "RGB":
        img = img.convert("RGB")

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

    # getvalue() is more efficient than seek(0) + read()
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
