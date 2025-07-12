"""WTForms forms used across blueprints."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import SelectField

ENGINE_CHOICES = [("veo","Veo 3 (Vertex AI)"),("hunyuan","HunyuanVideo (GKE)")]

class PromptForm(FlaskForm):
    prompt = StringField("Prompt", validators=[DataRequired()])
    engine = SelectField("Engine", choices=ENGINE_CHOICES, default="veo")
    submit = SubmitField("Generate Scene")

class RegistrationForm(FlaskForm):
    display_name = StringField("Display Name", validators=[DataRequired(), Length(max=80)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8)],
    )
    confirm = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class StoryCreateForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("Create Story")


class PromptForm(FlaskForm):
    prompt = StringField("Your next prompt", validators=[DataRequired()])
    submit = SubmitField("Generate Scene")