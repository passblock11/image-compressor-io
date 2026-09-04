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
    # Fast file size validation without reading entire file into a bytes string upfront
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

    try:
        # Open image directly from file stream to leverage lazy loading
        img = Image.open(file.file)

        MAX_WIDTH = 1600
        width, height = img.size

        # Resize large images
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))

            # Enable fast libjpeg downscaling during load if image is JPEG
            if img.format == "JPEG":
                img.draft("RGB", (MAX_WIDTH, new_height))

            # Convert unsupported color modes
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Use Image.BICUBIC filter for ~2-3x faster resizing compared to LANCZOS
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)
        elif img.mode in ("RGBA", "P"):
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

    # Use output.getvalue() to avoid unnecessary stream seeking and reading
    return Response(
        content=output.getvalue(),
        media_type="image/jpeg"
    )
