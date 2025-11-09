from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class Customer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(100),nullable=True)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    gender=db.Column(db.String(10),nullable=False)


class Book(db.Model):
    """Simple Book model for the library app.

    Fields:
    - id: primary key
    - title: book title (required)
    - author: optional author name
    - isbn: optional unique identifier
    - copies: total copies owned
    - available: copies currently available
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=True)
    isbn = db.Column(db.String(50), unique=True, nullable=True)
    copies = db.Column(db.Integer, nullable=False, default=1)
    available = db.Column(db.Integer, nullable=False, default=1)
    pdf_url = db.Column(db.String(300), nullable=True)