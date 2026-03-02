import numpy as np
import base64
import io
import binascii
import json
import h5py
from functools import lru_cache
from PIL import Image, ImageOps, ImageFilter
from tensorflow.keras.models import load_model, model_from_json
from django.conf import settings

#load the model only once and cache for faster prediction without reloading everytime user submits the digit
def _fix_input_layer_config(node):
    if isinstance(node, dict):
        class_name = node.get("class_name")
        config = node.get("config")
        if class_name == "InputLayer" and isinstance(config, dict):
            if "batch_shape" in config and "batch_input_shape" not in config:
                config["batch_input_shape"] = config.pop("batch_shape")
            config.pop("optional", None)

        if isinstance(config, dict):
            dtype_value = config.get("dtype")
            if isinstance(dtype_value, dict) and dtype_value.get("class_name") == "DTypePolicy":
                policy_config = dtype_value.get("config", {})
                config["dtype"] = policy_config.get("name", "float32")

            config.pop("quantization_config", None)

        for value in node.values():
            _fix_input_layer_config(value)
    elif isinstance(node, list):
        for item in node:
            _fix_input_layer_config(item)


def _load_h5_with_compat_fallback(model_path):
    with h5py.File(model_path, "r") as h5_file:
        raw_config = h5_file.attrs.get("model_config")
        if raw_config is None:
            raise ValueError("Missing model configuration in H5 file.")

    if isinstance(raw_config, bytes):
        raw_config = raw_config.decode("utf-8")

    config = json.loads(raw_config)
    _fix_input_layer_config(config)

    model = model_from_json(json.dumps(config))
    model.load_weights(model_path)
    return model


@lru_cache(maxsize=1)
def get_model():
    model_path = str(settings.BASE_DIR / "model" / "digit_model.h5")
    try:
        return load_model(model_path, compile=False)
    except Exception:
        return _load_h5_with_compat_fallback(model_path)
  
#check base64_image must be a string otherwise raise error
def preprocess_image(base64_image, debug=False):
    if not isinstance(base64_image, str):
        raise ValueError("Image payload must be a string.")

    payload = base64_image.strip()   #//check if URL is valid base64 data URL eg. data:image/png;base64, ......
    if ';base64,' not in payload:
        raise ValueError("Image payload must be a valid base64 data URL.")

    header, imgstr = payload.split(';base64,', 1)
    if not header.startswith("data:image"):
        raise ValueError("Only image data URLs are supported.")

    try:
        img_bytes = base64.b64decode(imgstr, validate=True)    #//convert string to bytes 
    except (binascii.Error, ValueError):
        raise ValueError("Image payload is not valid base64 data.")

    try:
        image = Image.open(io.BytesIO(img_bytes))  # // open the coverted bytes as an image 
    except Exception:
        raise ValueError("Unable to decode image bytes.")

    image = image.convert('L')   #/conver to grayscale with ('L')
    
    if debug:
        print(f"Original size: {image.size}")
        print(f"Original mode: {image.mode}")
    
    # Get bounding box of the drawn content to center it
    # Invert to get black on white for bbox detection
    inverted = ImageOps.invert(image)      
    bbox = inverted.getbbox()   # //getbox() returns bouding box ( left,top,right,bottom)

   # // if no drawing exists then error 
    if bbox is None:
        raise ValueError("Canvas is empty. Please draw a digit before submitting.")
    
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
