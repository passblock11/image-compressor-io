import pyvips
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response

app = FastAPI()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_WIDTH = 1600


@app.get("/")
def root():
    return {"message": "Image compression API running"}


@app.post("/compress")
def compress(file: UploadFile = File(...)):  # noqa: B008
    # Read file content synchronously
    image_bytes = file.file.read()

    # Validate file size
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

    try:
        # Load image via pyvips for high-performance memory-mapped decoding
        vimg = pyvips.Image.new_from_buffer(image_bytes, "")
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    try:
        # Convert CMYK to sRGB or flatten transparent alpha channels to white background
        if vimg.bands == 4 and getattr(vimg, "interpretation", None) == "cmyk":
            vimg = vimg.colourspace("srgb")
        elif vimg.bands in (2, 4):
            vimg = vimg.colourspace("srgb").flatten(background=[255, 255, 255])

        # Fast resize using thumbnail_image when width exceeds max width
        if vimg.width > MAX_WIDTH:
            vimg = vimg.thumbnail_image(MAX_WIDTH, height=10000000)

        # Encode image to JPEG with quality 80, Huffman table optimization, and progressive scan
        compressed_bytes = vimg.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True
        )

    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=compressed_bytes,
        media_type="image/jpeg"
    )
