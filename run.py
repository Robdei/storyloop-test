"""Local dev server using Flask-SocketIO."""
import eventlet

# Patch stdlib for eventlet first
eventlet.monkey_patch()

from app import create_app  # noqa: E402
from app.extensions import socketio  # noqa: E402


def main() -> None:  # noqa: D401
    """Run the development server."""
    app = create_app()
    # Use socketio.run instead of app.run
    socketio.run(app, debug=True, host="0.0.0.0", port=5002, use_reloader=True)


if __name__ == "__main__":
    main()