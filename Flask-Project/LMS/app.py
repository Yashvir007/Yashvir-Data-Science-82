import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from customer.models import db, Customer, Book
from send_mail import send_mail
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from functools import wraps

app = Flask(__name__)
# use absolute paths to avoid SQLite "unable to open database file" on Windows
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'pdfs')
# use local sqlite by default to avoid external MySQL access issues
db_dir = os.path.join(BASE_DIR, 'instance')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'lms.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key"

# Initialize SQLAlchemy
db.init_app(app)

with app.app_context():
    db.create_all()

# ------------------- HELPER DECORATORS -------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in first to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') != 'admin@gmail.com':
            flash("Access denied. Admins only.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# PDF Upload Route
@app.route('/upload_pdf', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    from werkzeug.utils import secure_filename
    pdf_url = None
    if request.method == 'POST':
        pdf = request.files.get('pdf')
        if pdf and pdf.filename.endswith('.pdf'):
            filename = secure_filename(pdf.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            pdf_path = os.path.join(upload_folder, filename)
            pdf.save(pdf_path)
            pdf_url = url_for('static', filename=f'pdfs/{filename}')
            flash('PDF uploaded successfully!', 'success')
        else:
            flash('Please select a valid PDF file.', 'danger')
    return render_template('upload_pdf.html', pdf_url=pdf_url)



# ------------------- ROUTES -------------------

@app.route("/")
def home():
    return render_template("home.html")


# ✅ Customer Registration
@app.route("/sign_up", methods=["GET", "POST"])
def customer_reg():
    if request.method == "POST":
        name = request.form.get("full-name")
        email = request.form.get("email")
        password = request.form.get("password")
        gender = request.form.get("gender")
        mobile = request.form.get("mobile")

        new_customer = Customer(
            name=name, email=email, password=password, gender=gender, phone=mobile
        )
        db.session.add(new_customer)
        db.session.commit()

        try:
            subject = "Welcome to My Library"
            body = f"Hi {name},\n\nThank you for registering at our library.\n\nRegards,\nLibrary Team"
            send_mail(email, subject, body)
        except Exception:
            pass

        return redirect(url_for("home"))
    return render_template("customer_reg.html")


# ✅ Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Admin login
        if email == "admin@gmail.com" and password == "123":
            session['user'] = email
            return redirect(url_for('all_customers'))

        # Customer login
        user = Customer.query.filter_by(email=email, password=password).first()
        if user:
            session['user'] = user.email
            return redirect(url_for("our_collection"))
        else:
            error = "Invalid email or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ✅ Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome {session['user']}! This is your dashboard."


# ✅ All Customers (Admin only)
@app.route("/all_customers")
@admin_required
def all_customers():
    customers = Customer.query.all()
    return render_template("all_customer.html", customers=customers)


# ✅ Delete All Customers (admin only)
@app.route("/delete_all_customers", methods=["POST"])
@admin_required
def delete_all_customers():
    try:
        Customer.query.delete()
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for("all_customers"))


# ✅ Search Customers (admin only)
@app.route("/search")
@admin_required
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return redirect(url_for('all_customers'))

    filters = [
        Customer.name.ilike(f"%{query}%"),
        Customer.email.ilike(f"%{query}%"),
        Customer.phone.ilike(f"%{query}%")
    ]
    if query.isdigit():
        filters.append(Customer.id == int(query))

    customers = Customer.query.filter(or_(*filters)).all()
    return render_template('all_customer.html', customers=customers)


# ------------------- BOOK ROUTES -------------------

@app.route('/books')
@admin_required
def books():
    all_books = Book.query.order_by(Book.title).all()
    return render_template('books.html', books=all_books)


# ✅ Our Collection — User must be logged in
@app.route('/our_collection')
@login_required
def our_collection():
    q = request.args.get('q', '').strip()
    if q:
        filters = [
            Book.title.ilike(f"%{q}%"),
            Book.author.ilike(f"%{q}%"),
            Book.isbn.ilike(f"%{q}%")
        ]
        books = Book.query.filter(or_(*filters)).order_by(Book.title).all()
    else:
        books = Book.query.order_by(Book.title).all()
    return render_template('our_collection.html', books=books, user=session.get('user'))



@app.route('/add_book', methods=['GET', 'POST'])
@admin_required
def add_book():
    from werkzeug.utils import secure_filename
    pdf_url = None
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn') or None
        try:
            copies = int(request.form.get('copies') or 1)
        except ValueError:
            copies = 1

        pdf = request.files.get('pdf')
        if pdf and pdf.filename.endswith('.pdf'):
            filename = secure_filename(pdf.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            pdf_path = os.path.join(upload_folder, filename)
            pdf.save(pdf_path)
            pdf_url = url_for('static', filename=f'pdfs/{filename}')
        else:
            pdf_url = None

        book = Book(title=title, author=author, isbn=isbn, copies=copies, available=copies, pdf_url=pdf_url)
        db.session.add(book)
        db.session.commit()
        return redirect(url_for('books'))
    return render_template('update_book.html', book=None, pdf_url=pdf_url)


@app.route('/update_book/<int:id>', methods=['GET', 'POST'])
@admin_required
def update_book(id):
    book = Book.query.get_or_404(id)
    from werkzeug.utils import secure_filename
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        isbn = request.form.get('isbn') or None
        book.isbn = isbn
        try:
            copies = int(request.form.get('copies') or book.copies)
        except ValueError:
            copies = book.copies
        diff = copies - book.copies
        book.copies = copies
        book.available = max(0, book.available + diff)
        pdf = request.files.get('pdf')
        if pdf and pdf.filename.endswith('.pdf'):
            filename = secure_filename(pdf.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            pdf_path = os.path.join(upload_folder, filename)
            pdf.save(pdf_path)
            book.pdf_url = url_for('static', filename=f'pdfs/{filename}')
        db.session.commit()
        return redirect(url_for('books'))
    return render_template('update_book.html', book=book)


@app.route('/delete_book/<int:id>', methods=['POST'])
@admin_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('books'))


@app.route('/buy_book/<int:id>')
@login_required
def buy_book(id):
    book = Book.query.get_or_404(id)
    if getattr(book, 'available', 0) > 0:
        book.available -= 1
        db.session.commit()
    else:
        flash('Book not available to buy', 'warning')
    return redirect(url_for('our_collection'))


@app.route('/rent_book/<int:id>')
@login_required
def rent_book(id):
    book = Book.query.get_or_404(id)
    if getattr(book, 'available', 0) > 0:
        book.available -= 1
        db.session.commit()
    else:
        flash('Book not available to rent', 'warning')
    return redirect(url_for('our_collection'))


# ✅ Customer update & delete
@app.route("/delete_customer/<int:id>", methods=["POST"])
@admin_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for("all_customers"))


@app.route("/update_customer/<int:id>", methods=["GET", "POST"])
@admin_required
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == "POST":
        customer.name = request.form.get("full-name")
        customer.email = request.form.get("email")
        customer.password = request.form.get("password")
        customer.gender = request.form.get("gender")
        customer.phone = request.form.get("mobile")
        db.session.commit()
        return redirect(url_for("all_customers"))
    return render_template("update_customer.html", customer=customer)
# Delete All Books Route
@app.route('/delete_all_books', methods=['POST'])
@admin_required
def delete_all_books():
    try:
        Book.query.delete()
        db.session.commit()
        flash('All books deleted!', 'warning')
    except Exception:
        db.session.rollback()
        flash('Error deleting books.', 'danger')
    return redirect(url_for('books'))



# ------------------- STATIC PAGES -------------------

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
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
    return render_template('privacy.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


# ✅ Register route (with hashing)
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


# ------------------- RUN APP -------------------

if __name__ == "__main__":
    app.run(debug=True)
