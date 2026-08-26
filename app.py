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
        # read uploaded file
        image_bytes = await file.read()

        # file size validation
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

        # try opening image
        img = Image.open(io.BytesIO(image_bytes))

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

    MAX_WIDTH = 1600
    width, height = img.size

    # OPTIMIZATION 1: Draft mode for JPEGs
    # Fast libjpeg DCT downscaling during initial load before full decode
    if width > MAX_WIDTH:
        target_height = int(height * (MAX_WIDTH / width))
        img.draft("RGB", (MAX_WIDTH, target_height))

    # convert unsupported modes
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size

    # OPTIMIZATION 2: BICUBIC resampling filter
    # Image.BICUBIC is ~2-3x faster than Image.LANCZOS with virtually identical visual quality
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
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

    # OPTIMIZATION 3: Return buffer directly via getvalue()
    # Avoids seeking back to 0 and re-reading the entire buffer payload
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
