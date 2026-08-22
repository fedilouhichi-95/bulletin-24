"""Bulletin 24 — Flask application factory."""

from pathlib import Path

from flask import Flask
from flask_compress import Compress

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    # Photos are content-stable: let browsers keep them for a year.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
    Compress(app)

    from . import routes

    app.register_blueprint(routes.bp)

    return app
