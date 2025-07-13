"""Blueprint providing register/login/logout views."""
from __future__ import annotations

import uuid, datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..tasks.email import send_welcome_email
from ..extensions import db
from ..forms import LoginForm, RegistrationForm
from ..models import User


auth_bp = Blueprint("auth", __name__, template_folder="../../templates")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():  # noqa: D401
    if current_user.is_authenticated:
        return redirect(url_for("story.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            display_name=form.display_name.data.strip(),
        )
        user.set_password(form.password.data)
        user.email_token = str(uuid.uuid4())
        user.token_sent_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        send_welcome_email(user)   # Celery task
        flash("Check your inbox to confirm your email.", "info")
        return redirect(url_for("auth.login"))
    if form.is_submitted() and not form.validate():
        flash(
            "Registration was unsuccessful. "
            "Ensure passwords match and have 8 or more characters.",
            "danger",
        )

    return render_template("auth/register.html", form=form)


@auth_bp.route("/verify/<token>")
def verify_email(token):
    user = User.query.filter_by(email_token=token).first_or_404()
    if user.is_active:
        flash("Account already verified — please log in.", "info")
        return redirect(url_for("auth.login"))

    user.is_active = True
    user.email_token = None        # one-time use
    db.session.commit()

    flash("Email verified — you can now log in!", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("story.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        # ⬇️  updated lookup + active check
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user and user.is_active and user.check_password(form.password.data):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("story.dashboard"))
        else:
            flash("Invalid credentials or email not verified.", "danger")
            # fall through → re-render form with flash

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():  # noqa: D401
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))