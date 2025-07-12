"""Blueprint providing register/login/logout views."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

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
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():  # noqa: D401
    if current_user.is_authenticated:
        return redirect(url_for("story.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user: User | None = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("story.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("auth/login_old.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():  # noqa: D401
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))