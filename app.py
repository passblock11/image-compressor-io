import io

import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008

    try:
        # Get file size using seek and tell to avoid reading full file into memory prematurely
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

        # read uploaded file
        image_bytes = file.file.read()

        # try opening image lazily
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except HTTPException:
        # Re-raise explicit HTTPExceptions
        raise

    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    MAX_WIDTH = 1600

    # resize large images
    if img.width > MAX_WIDTH:
        img = img.thumbnail_image(MAX_WIDTH, height=10000000)

    # convert/flatten transparent background if alpha exists
    if img.hasalpha():
        img = img.colourspace("srgb").flatten(background=[255, 255, 255])

    # compress image to progressive JPEG format
    output_bytes = img.jpegsave_buffer(
        Q=80,
        optimize_coding=True,
        strip=True,
        interlace=True
    )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
