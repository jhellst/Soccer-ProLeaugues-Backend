from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Email, Length, URL, Optional


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField(
        'Username',
        validators=[InputRequired(), Length(max=30)],
    )

    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=6, max=50)],
    )

    # TODO: Delete?
    # email = StringField(
    #     'E-mail',
    #     validators=[InputRequired(), Email(), Length(max=50)],
    # )



class LoginForm(FlaskForm):
    """Login form."""

    username = StringField(
        'Username',
        validators=[InputRequired(), Length(max=30)],
    )

    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=6, max=50)],
    )


class UserEditForm(FlaskForm):
    """Form for editing a user."""

    username = StringField(
        'Username',
        validators=[InputRequired(), Length(max=30)],
    )

    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=6, max=50)],
    )

    # TODO: Delete?
    # email = StringField(
    #     'E-mail',
    #     validators=[InputRequired(), Email(), Length(max=50)],
    # )


class CSRFProtection(FlaskForm):
    """CSRF protection"""
    # TODO: Add `pass`, which is empty class convention.
    #
    # Resources:
    # .   https://blog.finxter.com/5-best-ways-to-create-an-empty-class-in-python
    # .   https://stackoverflow.com/questions/61243808/whats-the-usage-of-empty-class-in-python