from flask_mail import Message
from app import app, mail
from flask import render_template


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_news_letter(user, requests):
    send_email('This Weeks Requests',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/news_letter.txt',
                                         user=user, requests=requests),
               html_body=render_template('email/news_letter.html',
                                         user=user, requests=requests))


def send_confirmation(email, template):
    msg = Message('SAAC Email Confirmation',
                  sender=app.config['ADMINS'][0],
                  recipients=[email],
                  html=template)
    mail.send(msg)

def send_response_email(email, template):
    msg = Message('Response to Your Request',
                  sender=app.config['ADMINS'][0],
                  recipients=[email],
                  html=template)
    mail.send(msg)