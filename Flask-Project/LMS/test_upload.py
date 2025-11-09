from app import app, db
from customer.models import Book
from io import BytesIO

with app.test_client() as client:
    # set admin session
    with client.session_transaction() as sess:
        sess['user'] = 'admin@gmail.com'

    data = {
        'title': 'Test PDF Book',
        'author': 'Unit Test',
        'isbn': 'TESTISBN123',
        'copies': '1',
        'pdf': (BytesIO(b'%PDF-1.4\n%Test PDF content\n'), 'test.pdf')
    }

    resp = client.post('/add_book', data=data, content_type='multipart/form-data', follow_redirects=True)
    print('POST /add_book status:', resp.status_code)

    # Query the DB for the book
    with app.app_context():
        b = Book.query.filter_by(isbn='TESTISBN123').first()
        if b:
            print('Book saved:', b.id, b.title, b.pdf_url)
        else:
            print('Book not found')
