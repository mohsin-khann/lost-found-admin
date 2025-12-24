import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', '').split(',')
    # NEW: secure password map (email → password)
    ADMIN_CREDENTIALS = {
        "admin@lostfound.com": "12345678", 
        "mohsin.codes1@gmail.com": "Mohsinkhan123"
    }