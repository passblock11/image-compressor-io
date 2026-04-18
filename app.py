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
    """
    Compresses an uploaded image using pyvips for high performance.
    """
    try:
        # read uploaded file
        image_bytes = file.file.read()

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

        # load image from buffer
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    MAX_WIDTH = 1600

    # resize large images using efficient thumbnailing
    if img.width > MAX_WIDTH:
        # thumbnail_image is much faster than traditional resize as it
        # performs shrink-on-load when supported by the underlying format
        img = img.thumbnail_image(MAX_WIDTH)

    # compress image to JPEG
    # Q=80 matches the original quality setting
    # optimize_coding=True matches optimize=True in Pillow
    # interlace=True matches progressive=True in Pillow
    output_buffer = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        interlace=True
    )

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
