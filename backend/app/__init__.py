import click
from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from config import Config
from app.extensions import cors, db, jwt, migrate


def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)

	db.init_app(app)
	migrate.init_app(app, db)
	jwt.init_app(app)

	cors.init_app(
		app,
		resources={
			r"/api/*": {
				"origins": app.config.get("CORS_ORIGINS", [
					"http://localhost:5173",
					"http://127.0.0.1:5173",
				]),
			}
		},
	)

	from app.models import AuditLog, Book, BorrowRequest, LibrarySetting, Loan, Notification, Penalty, User  # noqa: F401
	from app.routes.auth_routes import auth_bp
	from app.routes.book_routes import books_bp
	from app.routes.borrow_request_routes import borrow_requests_bp
	from app.routes.verification_routes import verification_bp
	from app.routes.notification_routes import notifications_bp
	from app.routes.audit_routes import audit_bp
	from app.routes.library_routes import library_bp
	from app.routes.borrower_routes import borrower_bp
	app.register_blueprint(auth_bp)
	app.register_blueprint(books_bp)
	app.register_blueprint(borrow_requests_bp)
	app.register_blueprint(verification_bp)
	app.register_blueprint(notifications_bp)
	app.register_blueprint(audit_bp)
	app.register_blueprint(library_bp)
	app.register_blueprint(borrower_bp)

	@app.cli.command("send-daily-emails")
	def send_daily_emails():
		from app.services.email_jobs import run_daily_email_notifications
		try:
			result = run_daily_email_notifications()
		except OperationalError as error:
			database_url = app.config.get("SQLALCHEMY_DATABASE_URI", "") or ""
			if "railway.internal" in database_url:
				raise click.ClickException(
					"The configured database uses Railway's private hostname, which is only "
					"reachable inside Railway. Run this job from a Railway scheduled service, "
					"or set LOCAL_DATABASE_URL (local MySQL) or DATABASE_PUBLIC_URL (Railway "
					"public TCP proxy) in backend/.env."
				) from error
			raise click.ClickException(f"Could not connect to the database: {error.orig}") from error
		print(f"Daily email job complete: {result}")

	@app.get("/")
	def index():
		return {
			"success": True,
			"message": "PCDS Library API is running",
			"health": "/api/health",
			"database_test": "/api/database/test",
		}, 200

	@app.get("/api")
	def api_root():
		return {
			"success": True,
			"message": "PCDS Library API is running",
			"routes": {
				"health": "/api/health",
				"database_test": "/api/database/test",
				"auth": "/api/auth",
				"books": "/api/books",
				"borrow_requests": "/api/borrow-requests",
			},
		}, 200

	@app.get("/api/health")
	def health():
		return {
			"success": True,
			"message": "PCDS Library API is running",
		}, 200

	@app.get("/api/database/test")
	def database_test():
		try:
			db.session.execute(text("SELECT 1"))
			return {
				"success": True,
				"message": "MySQL database connected successfully",
			}, 200
		except Exception as error:
			db.session.rollback()
			return {
				"success": False,
				"message": "Failed to connect to MySQL",
				"error": str(error),
			}, 500

	return app
