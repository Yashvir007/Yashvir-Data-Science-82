"""Minimal contact-only Flask application (separate file to avoid touching messy app.py)."""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from send_mail import send_mail


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'change-me-please')


@app.route('/')
def index():
    return redirect(url_for('contact'))


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


if __name__ == '__main__':
    app.run(debug=True)
