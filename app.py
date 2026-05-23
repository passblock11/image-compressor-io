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
        # file size validation using seek/tell to avoid reading whole file into memory if it's too large
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

        # Read the file content
        image_bytes = file.file.read()

        # Try opening image with pyvips
        # thumbnail_buffer is very efficient as it only decodes what's needed for the thumbnail
        MAX_WIDTH = 1600

        # size='down' ensures we don't upscale
        # high height to ensure we only constrain by width
        img = pyvips.Image.thumbnail_buffer(
            image_bytes,
            MAX_WIDTH,
            height=10000000,
            size='down'
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Upload failed: {str(e)}"
        )

    # Handle transparency by flattening onto a white background
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Compress image to JPEG buffer
    # interlace=True creates a progressive JPEG
    output_buffer = img.jpegsave_buffer(
        interlace=True,
        Q=80
    )

    return Response(
        content=output_buffer,
        media_type="image/jpeg"
    )
