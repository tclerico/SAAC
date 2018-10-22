from app import db, app, login
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from datetime import datetime
from time import time
import jwt


uTe = db.Table('UserToExpert',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('expertise_id', db.Integer, db.ForeignKey('expertise.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    class_year = db.Column(db.Integer)
    department = db.Column(db.String(120))
    sport = db.column(db.String(64))
    sec_sport = db.column(db.String(64))
    requests = db.relationship('Request', backref='author', lazy='dynamic')
    password_hash = db.Column(db.String(128))
    fields = db.relationship('Expertise', secondary=uTe, lazy='dynamic',
                                backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def expert(self, user):
        if not self.is_expert(user):
            self.expertise.append(user)

    def resign(self, user):
        if self.is_expert(user):
            self.expertise.remove(user)

    def is_expert(self, Expertise):
        return self.expertise.filter(
            uTe.c.ExpertId == Expertise.id).count() > 0

    #function returning all the request from current_users expertises
    def expert_requests(self):
        return Request.query.join(
            uTe, (uTe.c.expertise_id == Request.expertise)).join(
            User, (User.id == uTe.c.user_id)).filter(uTe.c.user_id == self.id).order_by(Request.timestamp.desc())

    #function returning all requests made by current_user
    def my_requests(self):
        return Request.query.filter(Request.uid == self.id).order_by(Request.timestamp.desc()).all()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))



class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    expertise = db.Column(db.Integer, db.ForeignKey('expertise.id'), index=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(560))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_active = db.Column(db.Boolean)

    def __repr__(self):
        return '{}'.format(self.title)



class Resolution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
    description = db.Column(db.String(64))

    def __repr__(self):
        return '<Resolution {}>'.format(self.description)

class Expertise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_prefix = db.Column(db.String(12), index=True)
    course_level = db.Column(db.Integer, index=True)

    def __repr__(self):
        return '{}'.format(self.course_prefix) + ' {}'.format(self.course_level)