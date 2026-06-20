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
        # read uploaded file
        # use file.file.read() as we are in a sync def
        image_bytes = file.file.read()

        # file size validation
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="File too large. Max allowed size is 100 MB"
            )

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # try opening image metadata to check width
        # This is lazy and fast
        img = pyvips.Image.new_from_buffer(image_bytes, "")

    except pyvips.Error:
        raise HTTPException(status_code=400, detail="Invalid image file")

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code=400, detail="Upload failed")

    MAX_WIDTH = 1600

    # resize large images using shrink-on-load if possible
    if img.width > MAX_WIDTH:
        # thumbnail_buffer is highly optimized for this task
        img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

    # handle transparency: convert to RGB by flattening against a white background
    if img.bands == 4 or img.bands == 2:
        img = img.flatten(background=[255, 255, 255])

    # compress image to JPEG buffer
    # Q=80 (quality), optimize_coding=True (optimize), interlace=True (progressive), strip=True (remove metadata)
    output_bytes = img.jpegsave_buffer(
        Q=80, optimize_coding=True, interlace=True, strip=True
    )

    return Response(content=output_bytes, media_type="image/jpeg")
