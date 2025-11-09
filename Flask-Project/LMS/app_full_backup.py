"""
Backup of the original app.py before reducing to contact-only.
"""
from pathlib import Path

src = Path(__file__).with_name('app.py')
print(f"This file is a backup copy. Original app.py path: {src}")
