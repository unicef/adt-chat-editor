import base64
from pathlib import Path

from src.settings import custom_logger


# Create the logger
logger = custom_logger("Image Utils")


def get_sample_cover_image() -> str:
    """
    Read the sample cover image and convert it to base64.

    Returns:
        str: Base64 encoded string of the image.
    """
    try:
        image_path = Path("data/samples/cover_image.png")
        with open(image_path, "rb") as f:
            image_data = f.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")
        return f"data:image/png;base64,{base64_image}"
    except Exception as e:
        logger.error(f"Error reading sample image: {e}")
        return ""
