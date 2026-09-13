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

        # load image with pyvips
        vimg = pyvips.Image.new_from_buffer(image_bytes, "")

        # convert unsupported/special color modes
        if vimg.interpretation in ("cmyk", "scmyk") or vimg.bands == 2:
            vimg = vimg.colourspace("srgb")

        MAX_WIDTH = 1600

        # resize large images with shrink-on-load speedup
        if vimg.width > MAX_WIDTH:
            vimg = vimg.thumbnail_image(MAX_WIDTH, height=10000000)

        # check for alpha channel and flatten transparency over white background
        has_alpha = False
        if hasattr(vimg, "hasalpha"):
            has_alpha = bool(vimg.hasalpha() if callable(vimg.hasalpha) else vimg.hasalpha)
        elif hasattr(vimg, "has_alpha"):
            has_alpha = bool(vimg.has_alpha)
        else:
            has_alpha = vimg.bands in (2, 4)

        if has_alpha:
            vimg = vimg.flatten(background=[255, 255, 255])

        # compress image to JPEG buffer
        output_bytes = vimg.jpegsave_buffer(
            Q=80,
            optimize_coding=True,
            interlace=True,
            subsample_mode="on"
        )

    except HTTPException:
        raise
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
        content=output_bytes,
        media_type="image/jpeg"
    )
