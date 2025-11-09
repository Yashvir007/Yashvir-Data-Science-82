import os
import importlib.util

# Load app.py as a module by path (avoids package import issues)
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app_path = os.path.join(root, 'app.py')
spec = importlib.util.spec_from_file_location('app_module', app_path)
mod = importlib.util.module_from_spec(spec)
import sys
# Ensure project root is on sys.path so package imports in app.py resolve
if root not in sys.path:
    sys.path.insert(0, root)

spec.loader.exec_module(mod)
app = getattr(mod, 'app')

with app.test_client() as c:
    res = c.get('/about')
    res = c.get('/')
    print('status', res.status_code)
    data = res.get_data(as_text=True)
    print('home contains img1.jpg:', 'img1.jpg' in data)
