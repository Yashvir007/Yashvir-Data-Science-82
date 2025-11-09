"""Simple smoke test using Flask test client to request /our_collection"""
import sys
import os
from importlib import import_module

# Add project root (parent of scripts/) to sys.path so imports work
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

app_module = import_module('app')
app = app_module.app

with app.test_client() as client:
    resp = client.get('/our_collection')
    print('STATUS', resp.status_code)
    if resp.status_code != 200:
        print(resp.get_data(as_text=True)[:2000])
        raise SystemExit(1)
    else:
        print('SMOKE_OK')
