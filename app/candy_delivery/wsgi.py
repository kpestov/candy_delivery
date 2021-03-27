"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import dotenv
from django.core.wsgi import get_wsgi_application

dotenv.load_dotenv()
application = get_wsgi_application()
