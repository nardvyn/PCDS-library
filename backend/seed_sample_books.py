from app import create_app
from app.extensions import db
from app.models.book import Book


SAMPLE_BOOKS = [
    {
        "title": "Introduction to Information Technology",
        "author": "William Stallings",
        "isbn": "9780135210642",
        "accession_number": "PCDS-BOOK-001",
        "category": "Information Technology",
        "publication_year": 2021,
        "total_copies": 3,
    },
    {
        "title": "Database System Concepts",
        "author": "Abraham Silberschatz",
        "isbn": "9780078022159",
        "accession_number": "PCDS-BOOK-002",
        "category": "Computer Science",
        "publication_year": 2019,
        "total_copies": 2,
    },
    {
        "title": "Fundamentals of Web Development",
        "author": "Randy Connolly",
        "isbn": "9780134481265",
        "accession_number": "PCDS-BOOK-003",
        "category": "Web Development",
        "publication_year": 2020,
        "total_copies": 4,
    },
    {
        "title": "The 7 Habits of Highly Effective People",
        "author": "Stephen R. Covey",
        "isbn": "9781982137274",
        "accession_number": "PCDS-BOOK-004",
        "category": "Personal Development",
        "publication_year": 2020,
        "total_copies": 2,
    },
    {
        "title": "English for Academic and Professional Purposes",
        "author": "Maria Lourdes S. Bautista",
        "isbn": "9789712369016",
        "accession_number": "PCDS-BOOK-005",
        "category": "Academic Reference",
        "publication_year": 2022,
        "total_copies": 3,
    },
]


app = create_app()
with app.app_context():
    added = 0
    for data in SAMPLE_BOOKS:
        if Book.query.filter_by(accession_number=data["accession_number"]).first():
            continue
        db.session.add(Book(**data, available_copies=data["total_copies"]))
        added += 1
    db.session.commit()
    print(f"Added {added} sample books. Total books: {Book.query.count()}.")
