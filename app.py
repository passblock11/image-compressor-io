from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):
    try:
        # Efficient file size validation using the file stream
        # This avoids reading the entire file into memory just for a size check
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

        # Use pyvips.Image.thumbnail_buffer for optimized loading and resizing
        # It only decodes what is necessary to produce the thumbnail (shrink-on-load)
        # We use a very large height to only constrain by width
        try:
            img = pyvips.Image.thumbnail_buffer(
                image_bytes,
                MAX_WIDTH,
                height=10000000,
                size='down'
            )

            # Ensure we flatten transparency for JPEG (which doesn't support alpha)
            # This mimics the previous PIL .convert("RGB") behavior
            if img.hasalpha():
                img = img.flatten(background=[255, 255, 255])

        except pyvips.Error as e:
            if "not in a known format" in str(e).lower() or "not a known format" in str(e).lower():
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            raise e

        # Compress image to JPEG format in a memory buffer
        # Quality 80, optimize_coding (huffman), interlace (progressive)
        output_buffer = img.write_to_buffer(
            ".jpg",
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException as e:
        # Re-raise HTTPException to preserve status code and detail
        raise e

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
