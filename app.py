from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips
import io

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):

    try:
        # file size validation using seek/tell for efficiency
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

        # try opening image
        try:
            img = pyvips.Image.new_from_buffer(image_bytes, "")
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

    except HTTPException as e:
        raise e

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    MAX_WIDTH = 1600

    # optimize resizing: use thumbnail_buffer for "shrink-on-load" if resizing is needed
    if img.width > MAX_WIDTH:
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH)

    # handle transparency (convert to RGB with white background)
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # compress image to JPEG buffer
    output_bytes = img.jpegsave_buffer(
        Q=80,
        interlace=True,
        strip=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )