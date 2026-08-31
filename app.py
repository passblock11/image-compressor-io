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
    # Read uploaded file
    image_bytes = await file.read()

    # File size validation
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Max allowed size is 100 MB"
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )

    try:
        # Pass BytesIO directly to Image.open
        bio = io.BytesIO(image_bytes)
        img = Image.open(bio)

        MAX_WIDTH = 1600

        # Performance Optimization: Enable JPEG draft mode to perform fast libjpeg downscaling on decode
        if img.format == "JPEG" and img.width > MAX_WIDTH:
            img.draft("RGB", (MAX_WIDTH, int(img.height * (MAX_WIDTH / img.width))))

        # Convert unsupported modes
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        width, height = img.size

        # Performance Optimization: Resize large images using Image.BICUBIC for fast high-quality resampling
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
            subsampling=2
        )

        # Performance Optimization: Avoid redundant seek/read by using output.getvalue() directly
        return Response(
            content=output.getvalue(),
            media_type="image/jpeg"
        )

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
