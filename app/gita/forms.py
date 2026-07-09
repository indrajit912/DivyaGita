from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ExplanationForm(FlaskForm):
    content = TextAreaField('Your Explanation / Commentary', validators=[
        DataRequired(message="Explanation content cannot be empty."),
        Length(min=10, max=10000, message="Explanation must be between 10 and 10,000 characters.")
    ])
    submit = SubmitField('Submit Explanation')
