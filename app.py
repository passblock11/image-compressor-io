import io
import pyvips
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):

    try:
        # file size validation without reading into memory
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

        # read uploaded file
        image_bytes = file.file.read()

        # try opening image with pyvips
        img = pyvips.Image.new_from_buffer(image_bytes, "")

        MAX_WIDTH = 1600
        # use thumbnail_buffer for efficient resizing if needed
        if img.width > MAX_WIDTH:
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

        # handle transparency (convert to RGB with white background)
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # compress image using pyvips for better performance
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTP exceptions to preserve status codes
        raise
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