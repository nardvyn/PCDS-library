import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def book_cover_folder():
	"""Store book covers on an attached Railway volume when available."""
	volume_mount = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
	if volume_mount:
		return os.path.join(volume_mount, "uploads", "book_covers")

	upload_folder = os.getenv(
		"UPLOAD_FOLDER",
		os.path.join(os.path.dirname(__file__), "app", "uploads", "school_ids"),
	)
	return os.path.join(os.path.dirname(upload_folder), "book_covers")


def database_url():
	"""Prefer a reachable database URL for the environment running the app."""
	if os.getenv("RAILWAY_ENVIRONMENT"):
		url = os.getenv("DATABASE_URL")
	else:
		url = (
			os.getenv("LOCAL_DATABASE_URL")
			or os.getenv("DATABASE_PUBLIC_URL")
			or os.getenv("MYSQL_PUBLIC_URL")
			or os.getenv("DATABASE_URL")
		)

	if url and url.startswith("mysql://"):
		return url.replace("mysql://", "mysql+pymysql://", 1)
	return url


class Config:
	SQLALCHEMY_DATABASE_URI = database_url()
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
	LIBRARY_OFFICIAL_EMAIL = os.getenv("LIBRARY_OFFICIAL_EMAIL", "pcds.libraries@gmail.com")
	PENALTY_ALERT_EMAIL = os.getenv("PENALTY_ALERT_EMAIL", "pcds.libraries@gmail.com")
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
	BOOK_COVER_FOLDER = book_cover_folder()
	MAX_CONTENT_LENGTH = 5 * 1024 * 1024
