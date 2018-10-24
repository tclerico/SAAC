from app import app, db, email
from app.email import *
from flask import render_template, flash, redirect, url_for, request, jsonify
from app.forms import LoginForm, NewRequestForm, RegistrationForm, ResetPasswordRequest, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Request, Expertise
from app.services import *
from collections import Counter
import datetime
import time
from datetime import date, datetime, timedelta


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        #creates user and logs them in
        register_user(form)
        return redirect(url_for('expertise'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET','POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequest()
    if form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


# route for adding expertise after registration
@app.route('/expertise', methods=['GET','POST'])
@login_required
def expertise():
    return render_template('expertise.html', title='Expertise')

# route to send content of subjects.txt to page with json
@app.route('/_populate')
def populate():
    # open file and read in lines
    subs=subjects_from_file()

    user = User.query.get(current_user.id)
    fields = list()
    for f in user.fields.all():
        str = '{}'.format(f.course_prefix) + '-{}'.format(f.course_level)
        fields.append(str)


    return jsonify(subjects=subs, fields=fields)

# sends a all of a users requests as a list to a page with json
@app.route('/_user_requests')
def user_requests():
    u = User.query.get(current_user.id)
    req = u.requests.filter_by(is_active=True).all()
    req_list = list()
    for r in req:
        req_list.append([r.id, r.title])

    return jsonify(requests=req_list)

# makes selected requests inactive so they won't be displayed
@app.route('/_removePost', methods=['GET','POST'])
def remove_post():
    if request.method == 'POST':
        received = request.json
        sent = []
        for r in received:
            id = int(r)
            sent.append(Request.query.get(id))

        for s in sent:
            s.is_active=False
        db.session.commit()

        nm = User.query.get(current_user.id)
        return jsonify(dict(redirect=url_for('account', name=nm.name)))


# route to process a change in a users expertise selections
# used in edit user and
@app.route('/_process', methods=['GET','POST'])
def process():
    # gets ajax request coupled with info
    if request.method == 'POST':
        # process select experise
        inputs = request.json
        process_expertise_change(inputs)
        return jsonify(dict(redirect=url_for('request_list')))


# route fo the users 'account' page where they can view their requests and edit info
# include ability to add and remove expertise and change password
@app.route('/account/<name>')
@login_required
def account(name):
    # get the current user and their requests
    user = User.query.filter_by(name=name).first()
    return render_template('user.html', user=user)


# route to display a specific request
@app.route('/request/<id>')
@login_required
def indiv_request(id):
    req = Request.query.get(id)
    return render_template('request.html', req=req)


# Route for the New Request Form to create a new request
@app.route('/new_request', methods=['GET', 'POST'])
@login_required
def new_request():
    form = NewRequestForm()
    if form.validate_on_submit():
        #creates new requet in service function and gets the requests id
        retId = create_new_request(form)
        flash('Successfully Created New Request')
        return redirect((url_for('indiv_request', id=retId)))
    return render_template('new_request.html', title='New Request', form=form)


# Route for list of requests
# (needs to fit the users preferences)
@app.route('/request_list')
@login_required
def request_list():
    requests = current_user.expert_requests().all()
    return render_template('requests.html', requests=requests)

# This route is specifially to test the email functionality
# and will need to be repurposed once scheduling is to be implemented
@app.route('/newsletter')
def newpostsemail():
    # get current user and all of the requests in their expertise
    id = current_user.id
    usr = User.query.get(id)
    reqs = usr.expert_requests().all()

    # loop evaluates the time each req was made,
    # if it was within the last week it is added to array
    toSend = []
    for r in reqs:
        if (datetime.utcnow()-timedelta(days=7)) <= r.timestamp:
            toSend.append(r)

    send_news_letter(usr, toSend)
    flash("News Letter Sent")
    return render_template('index.html')