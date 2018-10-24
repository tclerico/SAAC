import os
basedir = os.path.abspath(os.path.dirname(__file__))


def readin(file):
    with open(file) as f:
        lines = f.readlines()
    clean=[x.strip() for x in lines]

    return clean

class Config(object):
    key = readin('key.txt')
    emailInfo = readin('emailIn.txt')
    SECRET_KEY = os.environ.get('SECRET_KEY') or key[0]
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = emailInfo[0]
    MAIL_PASSWORD = emailInfo[1]
    ADMINS = ['saacithaca@gmail.com']


#python -m smtpd -n -c DebuggingServer localhost:8025