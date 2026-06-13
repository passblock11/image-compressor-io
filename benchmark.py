import time
import requests
import io
from PIL import Image

def create_test_image(size=(3000, 3000)):
    file = io.BytesIO()
    image = Image.new('RGB', size, color='red')
    image.save(file, 'JPEG')
    file.seek(0)
    return file

def benchmark():
    url = "http://127.0.0.1:8000/compress"
    img_file = create_test_image()

    files = {'file': ('test.jpg', img_file, 'image/jpeg')}

    # Warmup
    try:
        requests.post(url, files=files)
    except:
        print("Server not running?")
        return

    start_time = time.time()
    for _ in range(10):
        img_file.seek(0)
        requests.post(url, files=files)
    end_time = time.time()

    avg_time = (end_time - start_time) / 10
    print(f"Average time per request: {avg_time:.4f}s")

if __name__ == "__main__":
    benchmark()
