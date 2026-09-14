import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


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

        # Performance Optimization: Use libjpeg fast scaling during decode for JPEGs.
        # This significantly reduces memory usage and decode time before full resampling.
        if img.format == "JPEG":
            img.draft("RGB", (MAX_WIDTH, MAX_WIDTH))

    except HTTPException:
        raise

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

    # convert unsupported modes
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size

    # resize large images using BICUBIC filtering (faster than LANCZOS with negligible quality difference)
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

    # Performance Optimization: Use getvalue() directly to avoid redundant seeking and reading stream bytes.
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
