"""Almanach du Ciel Tunisien — Flask application factory."""

from pathlib import Path

from flask import Flask

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    from . import routes

    app.register_blueprint(routes.bp)

    return app
