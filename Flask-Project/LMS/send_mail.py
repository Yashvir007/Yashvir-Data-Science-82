"""Full LMS Flask application (secure minimal version, with built-in send_mail)."""

import os
import smtplib
from typing import Iterable, Tuple, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
# ---------------------------------
# Admin required decorator
# ---------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


# ---------------------------------
# Email sending utility (merged)
# ---------------------------------
def send_mail(recipient: Union[str, Iterable[str]], subject: str, body: str) -> Tuple[bool, str]:
    """Send an email via Gmail SMTP."""
    smtp_server = "smtp.gmail.com"
    port = 587

    sender_email = os.environ.get("SMTP_SENDER_EMAIL", "yashvirbbsc@gmail.com")
    sender_password = os.environ.get("SMTP_SENDER_PASSWORD", "wvcw cvnq zpmb xoqx")

    if isinstance(recipient, str):
        recipients = [recipient]
    else:
        recipients = list(recipient)

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ",".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        return True, "Mail sent successfully"
    except Exception as e:
        return False, str(e)


# ---------------------------------
# Flask App Configuration
# ---------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'change-me-please')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cookie security
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)


# ---------------------------------
# Database Models
# ---------------------------------
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    gender = db.Column(db.String(10), nullable=True)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=True)
    isbn = db.Column(db.String(50), unique=True, nullable=True)
    copies = db.Column(db.Integer, nullable=False, default=1)
    available = db.Column(db.Integer, nullable=False, default=1)


# Ensure DB tables exist
with app.app_context():
    db.create_all()


# ---------------------------------
# Routes
# ---------------------------------
@app.route('/')
def home():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('home.html')


@app.route('/about')
def about():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        message = (request.form.get('message') or '').strip()

        subject = f"Contact form message from {name or 'Anonymous'}"
        body = f"From: {name or 'Anonymous'} <{email or 'no-reply'}>\n\n{message}"

        try:
            success, resp = send_mail(
                os.environ.get('CONTACT_RECIPIENT', 'yashvirbbsc@gmail.com'),
                subject,
                body,
            )
            if success:
                flash('Your message has been sent. Thank you!', 'success')
            else:
                flash(f'Failed to send message: {resp}', 'danger')
        except Exception as e:
            flash(f'Error while sending message: {e}', 'danger')

        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/privacy')
def privacy():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('privacy.html')


@app.route('/faq')
def faq():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('faq.html')


# ---------------------------------
# Customer Management
# ---------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not (name and email and password):
            flash('Please fill all fields', 'warning')
            return redirect(url_for('register'))

        if Customer.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        cust = Customer(name=name, email=email, password=hashed)
        db.session.add(cust)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('customer_reg.html')


@app.route('/customer_reg', methods=['GET', 'POST'])
def customer_reg():
    return register()


@app.route('/update_customer/<int:id>', methods=['GET', 'POST'])
def update_customer(id):
    cust = Customer.query.get_or_404(id)
    if request.method == 'POST':
        cust.name = request.form.get('name') or cust.name
        cust.email = request.form.get('email') or cust.email
        cust.phone = request.form.get('phone') or cust.phone
        cust.gender = request.form.get('gender') or cust.gender
        db.session.commit()
        flash('Customer updated', 'success')
        return redirect(url_for('all_customers'))
    return render_template('update_customer.html', customer=cust)


@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    cust = Customer.query.get_or_404(id)
    db.session.delete(cust)
    db.session.commit()
    flash('Customer deleted', 'info')
    return redirect(url_for('all_customers'))


@app.route('/delete_all_customers', methods=['POST'])
def delete_all_customers():
    num = Customer.query.delete()
    db.session.commit()
    flash(f'Deleted {num} customers', 'warning')
    return redirect(url_for('all_customers'))


@app.route('/search')
def search():
    q = request.args.get('query', '').strip()
    if not q:
        return redirect(url_for('all_customers'))
    if q.isdigit():
        customers = Customer.query.filter((Customer.id == int(q)) | (Customer.phone.contains(q))).all()
    else:
        customers = Customer.query.filter((Customer.name.ilike(f'%{q}%')) | (Customer.email.ilike(f'%{q}%'))).all()
    return render_template('all_customer.html', customers=customers)


@app.route('/all_customers')
def all_customers():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    customers = Customer.query.order_by(Customer.id).all()
    return render_template('all_customer.html', customers=customers)


# ---------------------------------
# Book Management
# ---------------------------------
@app.route('/books')
@admin_required
def books():
    books = Book.query.order_by(Book.title).all()
    return render_template('books.html', books=books)


@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    isbn = request.form.get('isbn')
    copies = request.form.get('copies') or 1
    available = request.form.get('available') or copies

    try:
        copies = int(copies)
        available = int(available)
    except ValueError:
        copies = 1
        available = 1

    if not title:
        flash('Title is required', 'warning')
        return redirect(url_for('books'))

    if isbn and Book.query.filter_by(isbn=isbn).first():
        flash('Book with this ISBN already exists', 'danger')
        return redirect(url_for('books'))

    book = Book(title=title, author=author, isbn=isbn, copies=copies, available=available)
    db.session.add(book)
    db.session.commit()
    flash('Book added', 'success')
    return redirect(url_for('books'))


@app.route('/our_collection')
def our_collection():
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    if q:
        books = Book.query.filter(
            (Book.title.ilike(f"%{q}%")) |
            (Book.author.ilike(f"%{q}%")) |
            (Book.isbn.ilike(f"%{q}%"))
        ).all()
    else:
        books = Book.query.order_by(Book.title).all()
    return render_template('our_collection.html', books=books)


@app.route('/update_book/<int:id>', methods=['GET', 'POST'])
@admin_required
def update_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form.get('title') or book.title
        book.author = request.form.get('author') or book.author
        book.isbn = request.form.get('isbn') or book.isbn
        try:
            book.copies = int(request.form.get('copies') or book.copies)
        except ValueError:
            pass
        if book.available > book.copies:
            book.available = book.copies
        db.session.commit()
        flash('Book updated', 'success')
        return redirect(url_for('our_collection'))
    return render_template('update_book.html', book=book)


@app.route('/delete_book/<int:id>', methods=['POST'])
@admin_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted', 'info')
    return redirect(url_for('our_collection'))


@app.route('/buy_book/<int:id>')
def buy_book(id):
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    book = Book.query.get_or_404(id)
    if book.available > 0:
        book.available -= 1
        db.session.commit()
        flash('Purchase successful', 'success')
    else:
        flash('Book not available', 'warning')
    return redirect(url_for('our_collection'))


@app.route('/rent_book/<int:id>')
def rent_book(id):
    if not session.get('user_name') and not session.get('admin'):
        return redirect(url_for('login'))
    return buy_book(id)


# ---------------------------------
# Seeding demo data
# ---------------------------------
def seed_demo_data():
    from sqlalchemy.exc import IntegrityError
    if Customer.query.count() == 0:
        demo_customers = [
            Customer(name='Alice Kumar', email='alice@example.com', password=generate_password_hash('pass123')),
            Customer(name='Rahul Sharma', email='rahul@example.com', password=generate_password_hash('pass123')),
        ]
        for c in demo_customers:
            db.session.add(c)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    if Book.query.count() == 0:
        demo_books = [
            Book(title='The Great Gatsby', author='F. Scott Fitzgerald', isbn='9780743273565', copies=3, available=3),
            Book(title='To Kill a Mockingbird', author='Harper Lee', isbn='9780061120084', copies=2, available=2),
        ]
        for b in demo_books:
            db.session.add(b)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


with app.app_context():
    seed_demo_data()


# ---------------------------------
# Login & Admin
# ---------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Customer.query.filter_by(email=email).first()
        if user and user.password and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Logged in successfully', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('home'))


# Admin
def get_admin_credentials():
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@gmail.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', '123')
    return admin_email, admin_password


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
        admin_email, admin_password = get_admin_credentials()
        if email == admin_email and password == admin_password:
            session['admin'] = True
            session['admin_email'] = admin_email
            flash('Admin logged in', 'success')
            return redirect(url_for('all_customers'))
        flash('Invalid admin credentials', 'danger')
 

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_email', None)
    flash('Admin logged out', 'info')
    return redirect(url_for('home'))



@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_customers = Customer.query.count()
    total_books = Book.query.count()
    return render_template('admin_dashboard.html', customers=total_customers, books=total_books)


# ---------------------------------
# Run Application
# ---------------------------------
if __name__ == '__main__':
    if app.config['SECRET_KEY'] == 'change-me-please':
        print('⚠️ Warning: using default SECRET_KEY. Set FLASK_SECRET_KEY env var for production.')
    app.run(debug=True)
