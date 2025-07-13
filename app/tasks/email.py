from flask_mail import Message
from ..celery_app import celery_app
from ..extensions import mail, db
from ..models import User
from flask import current_app, url_for

@celery_app.task(name="tasks.send_welcome_email")
def send_welcome_email(user_id: int):
    app = current_app._get_current_object()   # ensure app context
    with app.app_context():
        user: User | None = db.session.get(User, user_id)
        if not user:
            return
        verify_url = url_for("auth.verify_email", token=user.email_token, _external=True)
        msg = Message(subject="Welcome to StoryLoop – confirm your email",
                      recipients=[user.email])
        msg.body = f"Hi {user.display_name},\n\nClick to verify: {verify_url}\n\nThanks!"
        mail.send(msg)