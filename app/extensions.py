"""Singleton extension instances."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_socketio import SocketIO
import os



db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()

# Initialize without app, will be initialized in create_app()
# socketio = SocketIO()
socketio = SocketIO(cors_allowed_origins="*", message_queue=os.getenv("REDIS_URL"))

