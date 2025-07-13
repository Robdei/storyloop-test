"""Local dev server using Flask-SocketIO."""
import eventlet
import os

# Patch stdlib for eventlet first
eventlet.monkey_patch()

from app import create_app  # noqa: E402
from app.extensions import socketio  # noqa: E402


def main() -> None:  # noqa: D401
    debug_mode = bool(int(os.getenv("FLASK_DEBUG", "1")))
    app = create_app()
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=debug_mode,
        use_reloader=debug_mode,
    )


if __name__ == "__main__":
    main()