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
        # early file size validation
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

        # try opening image from stream
        img = Image.open(file.file)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except HTTPException:
        # re-raise known HTTPExceptions
        raise

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
        # Use BICUBIC instead of LANCZOS for performance
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

    return Response(
        content=output.read(),
        media_type="image/jpeg"
    )
