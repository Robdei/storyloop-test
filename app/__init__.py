"""Application factory and blueprint registration."""
from __future__ import annotations

from flask import Flask

from .extensions import db, migrate, login_manager, csrf, socketio
from .config import Config

from .models import User  # noqa: E402

# Blueprints
from .routes.auth import auth_bp  # noqa: E402
from .routes.story import story_bp  # noqa: E402
from .routes.scene import scene_bp  # noqa: E402
from .routes.api import api_bp  # noqa: E402
from .routes.main import main_bp  # noqa: E402


def create_app(config_class: str | type[Config] | None = Config) -> Flask:
    """Factory pattern so tests can create isolated apps."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")  # Initialize SocketIO with the app

    # Blueprints
    app.register_blueprint(main_bp)  # Register main blueprint first
    app.register_blueprint(auth_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(scene_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:  # type: ignore[name-defined]
        return User.query.get(int(user_id))

    return app