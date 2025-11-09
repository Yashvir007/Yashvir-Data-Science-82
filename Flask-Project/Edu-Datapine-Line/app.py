from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import io

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# CSV path - adjust if necessary
CSV_PATH = r"C:\Users\yashv\BATCH82\MyPythonAssignment\student_cleaned.csv"


def load_students():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    # normalize
    df.columns = df.columns.str.strip().str.lower()
    return df


@app.route('/')
def index():
    if session.get('user'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Admin credentials (in-memory)
        ADMIN_EMAIL = 'admin@gmail.com'
        ADMIN_PASSWORD = '123'

        # If password provided and matches admin, log in as admin
        if password and email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user'] = {'email': ADMIN_EMAIL, 'id': 'admin', 'name': 'Administrator', 'is_admin': True}
            flash('Admin logged in.', 'success')
            return redirect(url_for('students'))

        df = load_students()
        if df.empty:
            flash('No student data found. Please register first.', 'warning')
            return redirect(url_for('register'))

        # match by email only for student login
        email_col = next((c for c in df.columns if 'email' in c), None)
        if email_col is None:
            flash('Email column not found in CSV.', 'danger')
            return redirect(url_for('login'))

        matched = df[df[email_col].astype(str).str.lower() == email]
        if not matched.empty:
            user = matched.iloc[0].to_dict()
            # verify stored password
            stored_pw = user.get('password')
            if not stored_pw:
                flash('No password set for this account. Contact admin.', 'danger')
                return redirect(url_for('login'))
            if not check_password_hash(stored_pw, password):
                flash('Invalid password.', 'danger')
                return redirect(url_for('login'))

            id_col = next((c for c in df.columns if c == 'id' or 'id' in c), None)
            session['user'] = {
                'email': user.get(email_col),
                'id': str(user.get(id_col)) if id_col else '',
                'name': user.get('name')
            }
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid credentials.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        df = load_students()
        # Ensure columns exist
        if df.empty:
            df = pd.DataFrame(columns=['name', 'email', 'id'])
        else:
            df.columns = df.columns.str.strip().str.lower()

        email_col = next((c for c in df.columns if 'email' in c), 'email')
        id_col = next((c for c in df.columns if c == 'id' or 'id' in c), 'id')

        # check duplicate email
        if not df.empty and (df[email_col].astype(str).str.lower() == email).any():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        # generate a new id: try numeric increment, otherwise use uuid
        if id_col in df.columns and not df.empty:
            try:
                max_id = pd.to_numeric(df[id_col], errors='coerce').dropna().astype(int).max()
                new_id = str(int(max_id) + 1) if pd.notna(max_id) else '1'
            except Exception:
                new_id = uuid.uuid4().hex[:8]
        else:
            new_id = uuid.uuid4().hex[:8]

        # store hashed password
        pw_hash = generate_password_hash(password)

        # append the new user
        new_row = {email_col: email, id_col: new_id, 'name': name, 'password': pw_hash}
        new_df = pd.DataFrame([new_row])
        # ensure new_df columns align with df
        for c in df.columns:
            if c not in new_df.columns:
                new_df[c] = None
        new_df = new_df[df.columns.tolist()]
        df = pd.concat([df, new_df], ignore_index=True)
        try:
            df.to_csv(CSV_PATH, index=False)
            flash('Account created. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Failed to save user: ' + str(e), 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)

    return wrapper


@app.route('/dashboard/')
@login_required
def dashboard():
    user = session.get('user')
    df = load_students()
    # show only the logged-in user's row
    email = user.get('email')
    if df.empty:
        student = None
    else:
        df.columns = df.columns.str.strip().str.lower()
        email_col = next((c for c in df.columns if 'email' in c), None)
        if email_col:
            matched = df[df[email_col].astype(str).str.lower() == str(email).lower()]
            student = matched.to_dict(orient='records')[0] if not matched.empty else None
        else:
            student = None

    return render_template('dashboard.html', user=user, student=student)


@app.route('/students/')
@login_required
def students():
    q = request.args.get('q', '').strip().lower()
    df = load_students()
    if df.empty:
        records = []
    else:
        # normalize columns
        df.columns = df.columns.str.strip().str.lower()
        if q:
            # build mask across all non-password columns
            mask = pd.Series([False] * len(df))
            for col in df.columns:
                if col == 'password':
                    continue
                mask = mask | df[col].astype(str).str.lower().str.contains(q, na=False)
            df = df[mask]
        records = df.to_dict(orient='records')

    return render_template('students.html', students=records, q=q)


@app.route('/students/edit/<student_id>/', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    user = session.get('user')
    if not user.get('is_admin'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('students'))

    df = load_students()
    if df.empty:
        flash('No student data found.', 'danger')
        return redirect(url_for('students'))

    df.columns = df.columns.str.strip().str.lower()
    id_col = next((c for c in df.columns if c == 'id' or 'id' in c), None)
    if not id_col:
        flash('ID column not found.', 'danger')
        return redirect(url_for('students'))

    matched = df[df[id_col].astype(str) == str(student_id)]
    if matched.empty:
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))

    student = matched.iloc[0].to_dict()

    # prepare columns for rendering (preserve CSV column order)
    columns = list(df.columns)
    id_col = id_col

    if request.method == 'POST':
        # update all columns from form
        idx = matched.index[0]
        for col in columns:
            if col == id_col:
                continue
            val = request.form.get(col)
            if val is None:
                continue
            val = val.strip()
            if col == 'password':
                if val:
                    df.at[idx, col] = generate_password_hash(val)
                # if empty, keep existing
            else:
                df.at[idx, col] = val

        try:
            df.to_csv(CSV_PATH, index=False)
            flash('Student updated.', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            flash('Failed to save changes: ' + str(e), 'danger')
            return redirect(url_for('edit_student', student_id=student_id))

    return render_template('edit_student.html', student=student, columns=columns, id_col=id_col)


@app.route('/students/<student_id>/download/')
@login_required
def download_student_pdf(student_id):
    # permission: admin or the same user
    user = session.get('user')
    df = load_students()
    if df.empty:
        flash('No student data available.', 'danger')
        return redirect(url_for('students'))

    df.columns = df.columns.str.strip().str.lower()
    id_col = next((c for c in df.columns if c == 'id' or 'id' in c), None)
    email_col = next((c for c in df.columns if 'email' in c), None)
    if not id_col:
        flash('ID column not found.', 'danger')
        return redirect(url_for('students'))

    matched = df[df[id_col].astype(str) == str(student_id)]
    if matched.empty:
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))

    student = matched.iloc[0].to_dict()

    # check permission
    if not (user.get('is_admin') or (email_col and user.get('email') and str(student.get(email_col)).lower() == str(user.get('email')).lower())):
        flash('You do not have permission to download this student PDF.', 'danger')
        return redirect(url_for('students'))

    # generate PDF using reportlab (import inside to avoid startup errors)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except Exception:
        flash('reportlab is required to generate PDFs. Install it: pip install reportlab', 'danger')
        return redirect(url_for('students'))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 50
    y = height - 50
    c.setFont('Helvetica-Bold', 16)
    c.drawString(x, y, f"Student Report: {student.get('name') or student.get(email_col) or student_id}")
    y -= 30
    c.setFont('Helvetica', 12)
    for k, v in student.items():
        if k == 'password':
            continue
        text = f"{k.capitalize()}: {v}"
        c.drawString(x, y, text)
        y -= 18
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont('Helvetica', 12)

    c.showPage()
    c.save()
    buffer.seek(0)
    return (buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'attachment; filename=student_{student_id}.pdf'
    })


@app.route('/logout/')
def logout():
    session.pop('user', None)
    flash('Logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
