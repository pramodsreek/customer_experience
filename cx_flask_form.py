#!/usr/bin/python3
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class TwitterHandleForm(FlaskForm):
    '''
    A class to handle fields and validation in a flask form.
    '''

    twitter_handle = StringField(
        "Enter your Twitter Handle", validators=[DataRequired(),\
        Length(min=5, max=10)]
    )
    competitors_twitter_handle = StringField(
        "Enter your Competitors Twitter Handle",
        validators=[DataRequired(), Length(min=5, max=10)],
    )
    twitter_handle_error = StringField("")
    twitter_handle_error.data = " "

    submit = SubmitField("Compare Sentiment and Classify Data")
