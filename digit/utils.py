import numpy as np
import base64
import io
from functools import lru_cache
from PIL import Image, ImageOps, ImageFilter
from tensorflow.keras.models import load_model
from django.conf import settings


@lru_cache(maxsize=1)
def get_model():
    return load_model(str(settings.BASE_DIR / "model" / "digit_model.h5"))


def preprocess_image(base64_image, debug=False):

    format, imgstr = base64_image.split(';base64,')
    img_bytes = base64.b64decode(imgstr)

    image = Image.open(io.BytesIO(img_bytes))
    image = image.convert('L')
    
    if debug:
        print(f"Original size: {image.size}")
        print(f"Original mode: {image.mode}")
    
    # Get bounding box of the drawn content to center it
    # Invert to get black on white for bbox detection
    inverted = ImageOps.invert(image)
    bbox = inverted.getbbox()
    
    if bbox:
        # Add padding around the digit
        padding = 20
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(image.width, bbox[2] + padding)
        bottom = min(image.height, bbox[3] + padding)
        
        # Crop to content
        image = image.crop((left, top, right, bottom))
        
        if debug:
            print(f"Cropped size: {image.size}")
    
    # Resize to 28x28 with high-quality downsampling
    image = image.resize((28, 28), Image.Resampling.LANCZOS)
    
    # Apply slight smoothing to reduce noise
    image = image.filter(ImageFilter.SMOOTH)

    image = np.array(image)
    
    if debug:
        print(f"After resize - Min: {image.min()}, Max: {image.max()}, Mean: {image.mean():.2f}")
        print(f"Non-white pixels: {np.sum(image < 250)}")

    # Invert: black strokes on white -> white strokes on black (MNIST style)
    image = 255 - image
    
    # Normalize to [0, 1]
    image = image / 255.0

    if debug:
        print(f"After invert & normalize - Min: {image.min():.3f}, Max: {image.max():.3f}, Mean: {image.mean():.3f}")
        print(f"Active pixels (>0.1): {np.sum(image > 0.1)}")

    image = image.reshape(1, 28, 28, 1)

    return image


def predict_digit(processed_image):
    model = get_model()
    prediction = model.predict(processed_image, verbose=0)
    digit = np.argmax(prediction)
    return digit
