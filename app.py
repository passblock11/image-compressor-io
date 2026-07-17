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
    # File validation
    try:
        # Check size and emptiness synchronously via seek and tell
        file.file.seek(0, io.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Max allowed size is 100 MB"
            )

        # Read the file content
        image_bytes = file.file.read()

        # Try opening image using pyvips
        # pyvips.Image.new_from_buffer lazily reads file headers to check validity
        img = pyvips.Image.new_from_buffer(image_bytes, "")
    except HTTPException:
        # Re-raise HTTPExceptions directly to prevent them from being swallowed
        raise
    except pyvips.Error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    # Convert/resize image
    try:
        width = img.width
        MAX_WIDTH = 1600

        # Resize using pyvips thumbnail_buffer if width exceeds MAX_WIDTH
        if width > MAX_WIDTH:
            # We configure height to be extremely large to make only width constrained,
            # preserving the aspect ratio.
            img = pyvips.Image.thumbnail_buffer(image_bytes, MAX_WIDTH, height=10000000)

        # Flatten alpha channels to white background if they exist
        if img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        # Ensure consistent color output
        img = img.colourspace("srgb")

        # Compress to JPEG
        # Q sets quality, optimize_coding optimizes Huffman table,
        # interlace generates a progressive JPEG, and strip removes EXIF/ICC metadata.
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
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Upload failed"
        )

    return Response(
        content=output_bytes,
        media_type="image/jpeg"
    )
