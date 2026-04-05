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
async def compress(file: UploadFile = File(...)):

    try:
        # Seek to the end of the file to determine size without reading into memory
        file.file.seek(0, 2)
        file_size = file.file.tell()
        # Reset file pointer to the beginning for subsequent reading
        file.file.seek(0)

        # file size validation
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

        # try opening image directly from file stream to avoid redundant memory buffering
        img = Image.open(file.file)

    except HTTPException:
        # Re-raise HTTPExceptions to prevent them from being caught by the generic Exception block
        raise

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # convert unsupported modes
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size

    MAX_WIDTH = 1600

    # resize large images
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        # Use BICUBIC resampling for a better balance of performance and quality compared to LANCZOS
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

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

    output.seek(0)
# //changes 
    return Response(
        content=output.read(),
        media_type="image/jpeg"
    )