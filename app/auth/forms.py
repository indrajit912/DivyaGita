from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp
from app.models.user import User

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[DataRequired(message="Please enter your username or email.")])
    password = PasswordField('Password', validators=[DataRequired(message="Please enter your password.")])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Please enter your full name."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    username = StringField('Username', validators=[
        DataRequired(message="Please enter a username."),
        Length(min=3, max=64, message="Username must be between 3 and 64 characters."),
        Regexp(r'^[a-zA-Z0-9_-]+$', message="Username must contain only letters, numbers, underscores, or hyphens.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Please enter your email address."),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Please enter a password."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    contact_number = StringField('Contact Number (Optional)', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address (Optional)', validators=[Optional(), Length(max=255)])
    privacy_agreement = BooleanField('I agree to the privacy policy', validators=[
        DataRequired(message="You must accept the privacy policy to register.")
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.lower().strip()).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower().strip()).first()
        if user:
            raise ValidationError('That email is already registered. Please log in or reset your password.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Please enter your email address."),
        Email(message="Please enter a valid email address.")
    ])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(message="Please enter a new password."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Reset Password')
