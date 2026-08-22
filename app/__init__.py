"""Bulletin 24 — Flask application factory."""

from pathlib import Path

from flask import Flask, Response
from flask_compress import Compress

BASE_DIR = Path(__file__).resolve().parent.parent

# Hardened per HTTP Observatory. App-level hook on purpose: blueprint
# after_request callbacks never fire for Flask's static file view.
# Inline CSS bundle -> style-src 'unsafe-inline' (perf decision).
# LQIP placeholders + SVG favicon -> img-src data:.
# main.js is same-origin and <script type="speculationrules"> is a data
# block, not executable code, so script-src 'self' needs no exceptions.
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(self)",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    # Photos are content-stable: let browsers keep them for a year.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
    Compress(app)

    @app.after_request
    def set_security_headers(resp: Response) -> Response:
        resp.headers.update(SECURITY_HEADERS)
        return resp

    from . import routes

    app.register_blueprint(routes.bp)

    return app
