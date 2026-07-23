from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import pyvips

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
async def compress(file: UploadFile = File(...)):

    try:
        # read uploaded file
        image_bytes = await file.read()

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

        # try opening image using pyvips
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    except HTTPException:
        # Re-raise HTTPExceptions we raised
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Check image dimensions
    width = img.width

    MAX_WIDTH = 1600

    # resize large images using pyvips
    # pyvips.Image.thumbnail_buffer is highly optimized because of shrink-on-load.
    # Note: thumbnail_buffer in pyvips 3.1.1/8.15 does not support 'no_upscale'.
    # We only call thumbnail_buffer if width is greater than MAX_WIDTH.
    # To keep original aspect ratio behavior, we set height to a very large number.
    if width > MAX_WIDTH:
        try:
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)
        except pyvips.Error:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file or processing error"
            )

    # convert unsupported modes / flatten alpha channels
    # In pyvips, hasalpha returns 1 if alpha exists, 0 otherwise
    if img.hasalpha():
        img = img.flatten(background=[255, 255, 255])

    # Convert to standard sRGB color space to ensure compatibility
    img = img.colourspace("srgb")

    try:
        # compress image to progressive JPEG buffer
        # interlace=True represents progressive JPEG, matching progressive=True in Pillow
        # Q=80 matches quality=80 in Pillow
        # optimize_coding=True matches optimize=True in Pillow
        # strip=True removes metadata to further reduce size
        output_bytes = img.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            strip=True
        )
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file or processing error"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
