#!/usr/bin/env python
"""
Production startup script for Django application
Uses gunicorn for production deployment
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty.settings')

# Import Django
import django
django.setup()

# Import and run gunicorn
from gunicorn.app.wsgiapp import WSGIApplication

class DjangoApplication(WSGIApplication):
    def __init__(self):
        self.application = None
        self.options = {}
        self.do_load_config()
        
    def load_config(self):
        config = {
            'bind': '0.0.0.0:8000',
            'workers': 2,
            'worker_class': 'sync',
            'worker_connections': 1000,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'timeout': 30,
            'keepalive': 2,
            'preload_app': True,
        }
        
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

if __name__ == '__main__':
    DjangoApplication().run()
