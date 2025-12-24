import cloudinary
import cloudinary.uploader
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def configure_cloudinary():
    cloudinary.config(
        cloud_name=Config.CLOUDINARY_CLOUD_NAME,
        api_key=Config.CLOUDINARY_API_KEY,
        api_secret=Config.CLOUDINARY_API_SECRET,
        secure=True
    )

def delete_image(public_id):
    try:
        configure_cloudinary()
        result = cloudinary.uploader.destroy(public_id)
        if result.get('result') == 'ok':
            logging.info(f"Deleted image: {public_id}")
            return True
        else:
            logging.error(f"Failed to delete image: {result}")
            return False
    except Exception as e:
        logging.error(f"Cloudinary error: {e}")
        return False