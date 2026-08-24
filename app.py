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
    # Validate file size via stream seek/tell without reading all bytes into memory upfront
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
        # Pass file object directly to Image.open to exploit lazy loading
        img = Image.open(file.file)

        MAX_WIDTH = 1600
        width, height = img.size

        # Fast downscaling during JPEG decoding if image is JPEG and width > MAX_WIDTH
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            if getattr(img, "format", None) == "JPEG":
                try:
                    img.draft("RGB", (MAX_WIDTH, new_height))
                except Exception:  # noqa: BLE001, S110
                    pass
            # Re-read dimensions after draft
            width, height = img.size
            if width > MAX_WIDTH:
                new_height = int(height * (MAX_WIDTH / width))
                # Use BICUBIC resampling for ~20-30% faster resize vs LANCZOS with imperceptible quality difference
                img = img.resize((MAX_WIDTH, new_height), Image.Resampling.BICUBIC)

        # convert unsupported modes
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

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
        content=output.getvalue(),
        media_type="image/jpeg"
    )
