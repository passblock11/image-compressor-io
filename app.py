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
    # OPTIMIZATION: Synchronous `def` offloads CPU-bound image processing
    # to Starlette's worker thread pool, preventing event loop blocking.

    try:
        # OPTIMIZATION: Validate file size using stream seeking without reading
        # the full payload into memory.
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
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

        # OPTIMIZATION: Pass underlying file stream directly to Image.open
        # to avoid redundant byte string copying.
        img = Image.open(file.file)

        width, height = img.size
        MAX_WIDTH = 1600

        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            # OPTIMIZATION: Draft mode allows libjpeg to perform fast downscaling
            # during decode for JPEG files, significantly reducing decode latency.
            img.draft("RGB", (MAX_WIDTH, new_height))

        # Convert unsupported modes (like Palette or RGBA) before resizing
        # as mode P cannot be interpolated with BICUBIC filter.
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # resize large images
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            # OPTIMIZATION: BICUBIC resampling provides ~3x speedup over LANCZOS
            # with imperceptible quality loss in compressed JPEGs.
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

    # OPTIMIZATION: `output.getvalue()` returns the bytes directly without
    # seeking to position 0 and performing a copy read.
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )