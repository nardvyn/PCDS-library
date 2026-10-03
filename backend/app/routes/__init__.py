from app.routes.auth_routes import auth_bp
from app.routes.book_routes import books_bp
from app.routes.borrow_request_routes import borrow_requests_bp

__all__ = ["auth_bp", "books_bp", "borrow_requests_bp"]
