import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
	SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
	JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
	GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
	STAFF_REGISTRATION_CODE = os.getenv("STAFF_REGISTRATION_CODE")
	MAIL_SERVER = os.getenv("MAIL_SERVER", "")
	MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
	MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
	MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
	MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")
	MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
	MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
	FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
	CORS_ORIGINS = [
		origin.strip()
		for origin in (
			os.getenv("CORS_ORIGINS", "").split(",")
			+ [
				"https://pcds-library.vercel.app",
				"http://localhost:5173",
				"http://127.0.0.1:5173",
			]
		)
		if origin.strip()
	]
	UPLOAD_FOLDER = os.getenv(
		"UPLOAD_FOLDER",
		os.path.join(os.path.dirname(__file__), "app", "uploads", "school_ids"),
	)
	MAX_CONTENT_LENGTH = 5 * 1024 * 1024
