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
        # Check file size efficiently without buffering entire file in memory
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        # File size validation
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

        # Open image stream directly (exploits PIL lazy-loading & avoids byte string copies)
        img = Image.open(file.file)

        # Use draft mode for fast JPEG decoder downscaling before full decode
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

    # Convert unsupported color modes
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = img.size

    # Resize large images using BICUBIC for ~3-4x faster processing than LANCZOS
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

    output = io.BytesIO()

    # Compress and export image
    img.save(
        output,
        format="JPEG",
        quality=80,
        optimize=True,
        progressive=True,
        subsampling=2
    )

    # Return output buffer directly without redundant seek/read operations
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
