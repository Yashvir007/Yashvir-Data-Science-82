"""Compile all Python files in the workspace to surface syntax errors."""
import os, py_compile, sys
base = r'C:\Users\yashv\Desktop\Batch82\LMS1'
errors = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except Exception as e:
                errors.append((path, str(e)))
if not errors:
    print('COMPILE_OK')
else:
    print('COMPILE_ERRORS')
    for p, e in errors:
        print(p)
        print('  ', e)
    sys.exit(1)
