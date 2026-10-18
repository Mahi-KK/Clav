import os

from flask import Flask

MAX_BODY_BYTES = 100 * 1024


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES
    app.config["APP_VERSION"] = os.environ.get("APP_VERSION", "dev")

    from .routes import bp
    app.register_blueprint(bp)
    return app
