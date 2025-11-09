"""Check books in DB and print rows for debugging."""
from app import app
from customer.models import Book

with app.app_context():
    books = Book.query.all()
    print(f"Found {len(books)} books")
    for b in books:
        print(b.id, b.title, getattr(b, 'pdf_url', None))
