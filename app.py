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
        # Efficient file size validation using seek/tell to avoid loading into memory
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

        # Open image directly from the file stream
        img = Image.open(file.file)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        # Re-raise HTTP exceptions to prevent them from being caught by the generic block
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    width, height = img.size
    MAX_WIDTH = 1600

    # Resize large images first if needed
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        # Use BICUBIC resampling for better speed while maintaining quality
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    # Convert to RGB AFTER potential resize to minimize the number of pixels processed
    if img.mode in ("RGBA", "P"):
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

    # Use getvalue() to return the buffer content efficiently
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
