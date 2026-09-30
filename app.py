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
        # Validate file size efficiently without reading full stream into memory
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

        # Open image directly from file stream to exploit lazy loading
        img = Image.open(file.file)

        MAX_WIDTH = 1600
        width, height = img.size

        # Apply fast libjpeg decode draft for large JPEGs before full load
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            img.draft("RGB", (MAX_WIDTH, new_height))

        # Convert non-RGB modes to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if width still exceeds MAX_WIDTH using BICUBIC for high speed & quality
        width, height = img.size
        if width > MAX_WIDTH:
            new_height = int(height * (MAX_WIDTH / width))
            img = img.resize((MAX_WIDTH, new_height), Image.BICUBIC)

        output = io.BytesIO()

        # Compress image to JPEG format
        img.save(
            output,
            format="JPEG",
            quality=80,
            optimize=True,
            progressive=True,
            subsampling=2
        )

        return Response(
            content=output.getvalue(),
            media_type="image/jpeg"
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
