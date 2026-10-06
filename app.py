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
    # Synchronous 'def' offloads CPU-bound image operations to Starlette worker threadpool
    try:
        # Check file size efficiently without reading full payload into memory
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

        # Open image stream directly to enable lazy loading
        img = Image.open(file.file)

        width, height = img.size
        MAX_WIDTH = 1600

        # Apply fast JPEG decoder downscaling during load if image exceeds MAX_WIDTH
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            if img.format == "JPEG":
                img.draft("RGB", (MAX_WIDTH, new_height))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            width, height = img.size
            if width > MAX_WIDTH:
                img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)
        elif img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

    except HTTPException:
        # Re-raise HTTP exceptions to avoid masking 413/400 errors
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

    # Return buffer bytes directly avoiding redundant seek/read calls
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
