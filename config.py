import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def readin(file):
    with open(file) as f:
        lines = f.readlines()
    clean=[x.strip() for x in lines]

    return clean

class Config(object):
    # key = os.environ.ge
    # emailInfo = readin('emailIn.txt')
    # salt = readin('passwdSalt.txt')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.environ.get('PASSWORD_SALT')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['saacithaca@gmail.com']
    LOG_TO_STDOU = os.environ.get('LOG_TO_STDOUT')


#python -m smtpd -n -c DebuggingServer localhost:8025

# returns all users for a specified expertise
# User.query.join(User.fields).filter_by(id=20).all()
