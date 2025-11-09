"""Load all templates to detect TemplateSyntaxError."""
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
import os, sys
p = r'C:\Users\yashv\Desktop\Batch82\LMS1\templates'
env = Environment(loader=FileSystemLoader(p))
errors = []
for root, dirs, files in os.walk(p):
    for f in files:
        if f.endswith('.html'):
            rel = os.path.relpath(os.path.join(root, f), p)
            try:
                env.get_template(rel.replace('\\\\','/'))
            except TemplateSyntaxError as e:
                errors.append((rel, str(e)))
            except Exception as e:
                errors.append((rel, str(e)))
if not errors:
    print('TEMPLATES_OK')
else:
    print('TEMPLATE_ERRORS')
    for r, e in errors:
        print(r)
        print('  ', e)
    sys.exit(1)
