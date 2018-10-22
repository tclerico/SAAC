from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, SelectField, Field
from wtforms.validators import  DataRequired, Email, EqualTo, ValidationError
from app.models import User, Expertise


#custom validator to ensure email entered is '@ithaca.edu'
class icEmail(object):
    def __init__(self, email="ithaca.edu", message=None):
        self.email = email
        if not message:
            message = u'Pleas use your ithaca.edu email'
        self.message = message

    def __call__(self, form, field):
        #takes form data and parses for the address
        emailIn = field.data
        emailArr = emailIn.split("@")
        email = emailArr[1]

        if email != self.email :
            raise ValidationError(self.message)


icmail = icEmail


#login form class
class LoginForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


#new request form class
class NewRequestForm(FlaskForm):
    #subject = StringField('Subject', validators=[DataRequired()])
    c_prefix = StringField('Course Prefix', validators=[DataRequired()])
    c_number = IntegerField('Course Number', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')


#registration form class
class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), icmail()])
    class_year = IntegerField('Class Year', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    sport = StringField('Sport', validators=[DataRequired()])
    sec_sport = StringField('Second Sport')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('That email is already in use')


class ResetPasswordRequest(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), icmail()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class ResolutionForm(FlaskForm):
    #TODO
    randomstuff =SelectField()