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
    Compresses an image using pyvips for high performance.
    Uses stream-based loading and optimized JPEG parameters.
    """
    try:
        # Validate file size without reading entire file into memory
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

        # Custom source for pyvips to read from UploadFile.file
        source = pyvips.SourceCustom()
        source.on_read(lambda bytes_to_read: file.file.read(bytes_to_read))
        source.on_seek(lambda offset, whence: file.file.seek(offset, whence))

        try:
            # Use access="sequential" for memory efficiency
            img = pyvips.Image.new_from_source(source, "", access="sequential")
        except pyvips.Error:
             raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        MAX_WIDTH = 1600

        # Optimized resize using thumbnail_image (uses shrink-on-load if possible)
        if img.width > MAX_WIDTH:
            img = img.thumbnail_image(MAX_WIDTH)

        # Save to buffer with optimized JPEG parameters
        output_buffer = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode='on'
        )

        return Response(
            content=output_buffer,
            media_type="image/jpeg"
        )

    except HTTPException:
        # Re-raise HTTPExceptions to avoid them being caught by the generic Exception block
        raise
    except Exception as e:
        print(f"Compression error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )
