"""WSGI entry point for production servers (waitress / gunicorn).

Usage:
    waitress-serve --host=0.0.0.0 --port=5055 wsgi:app      (Windows)
    gunicorn --bind 0.0.0.0:5055 wsgi:app                   (Linux)
"""
from app import app

if __name__ == "__main__":
    app.run()
