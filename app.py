from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    try:
        # file size validation without reading everything into memory
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

        image_bytes = file.file.read()

        # Load image using pyvips
        # thumbnail_buffer is very fast as it only decodes what's needed for the target size
        # We use a max width of 1600 as per original requirements
        img = pyvips.Image.thumbnail_buffer(image_bytes, 1600)

        # Ensure functional parity: Flatten alpha channels onto white background for JPEG
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Save to buffer as progressive JPEG with quality 80
        # interlace=True creates a progressive JPEG
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException as e:
        # Re-raise HTTPExceptions to avoid them being caught by the generic except block
        raise e

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
