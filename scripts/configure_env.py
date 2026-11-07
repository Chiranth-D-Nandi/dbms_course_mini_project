"""Replace the public development signing key while preserving local database credentials."""
import secrets
from pathlib import Path
from dotenv import dotenv_values, set_key

path = Path(__file__).resolve().parents[1] / '.env'
if not path.exists():
    raise SystemExit('Create .env from .env.example and set the MySQL credentials first.')
current = dotenv_values(path).get('DJANGO_SECRET_KEY', '') or ''
if not current or current.startswith(('django-insecure', 'local-development-only')):
    set_key(path, 'DJANGO_SECRET_KEY', secrets.token_urlsafe(48))
    print('Generated a private local Django signing key.')
else:
    print('Existing Django signing key preserved.')
