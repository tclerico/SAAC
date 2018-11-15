from app import app, db, email
from app.email import *
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from app.forms import LoginForm, NewRequestForm, RegistrationForm, ResetPasswordRequest, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Request, Expertise
from app.services import *
from collections import Counter
import datetime
import time
from datetime import date, datetime, timedelta
from app.token import *
from app.decorators import *


@app.before_first_request
def expertise_population():
    current_app.expert_population = count_population()


@app.before_first_request
def populate_expertise_table():
    subs = subjects_from_file()
    for s in subs:
        prefix = s[1]
        n100 = Expertise(course_prefix=prefix, course_level=100)
        n200 = Expertise(course_prefix=prefix, course_level=200)
        n300 = Expertise(course_prefix=prefix, course_level=300)
        n400 = Expertise(course_prefix=prefix, course_level=400)
        db.session.add(n100)
        db.session.add(n200)
        db.session.add(n300)
        db.session.add(n400)
        db.session.commit()


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
        user = register_user(form)

        token = generate_confirmation_token(user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('email/confirmation_email.html', confirm_url=confirm_url)
        send_confirmation(user.email, html)

        flash('Thank you for registering!')
        login_user(user)

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


@app.route('/confirm/<token>', methods=['GET', 'POST'])
@login_required
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')

    user = User.query.filter_by(email=email).first()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('index'))


@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for(account,name=current_user.name))
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')


@app.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('confirm_email',token=token, _external=True)
    html = render_template('email/confirmation_email.html',confirm_url=confirm_url)
    send_confirmation(current_user.email, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('unconfirmed'))


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
# used in edit user and expertise form
@app.route('/_process', methods=['GET','POST'])
def process():
    # gets ajax request coupled with info
    if request.method == 'POST':
        # process selected expertise
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
@check_confirmed
def indiv_request(id):
    req = Request.query.get(id)
    return render_template('request.html', req=req)


# Route for the New Request Form to create a new request
@app.route('/new_request', methods=['GET', 'POST'])
@login_required
@check_confirmed
def new_request():
    form = NewRequestForm()
    if form.validate_on_submit():
        #check to see if course info is correct
        checkInfo = validRequest(form)
        if checkInfo is False:
            flash('Incorrect Course Information')
            return redirect(url_for('new_request'))

        #creates new request in service function and gets the requests id
        returned_Id = create_new_request(form)
        flash('Successfully Created New Request')
        return redirect((url_for('indiv_request', id=returned_Id)))
    return render_template('new_request.html', title='New Request', form=form)


# Route for list of requests
# (needs to fit the users preferences)
@app.route('/request_list', methods=['GET','POST'])
@login_required
@check_confirmed
def request_list():
    rFu = current_user.expert_requests().all()
    requests = sort_requests(rFu)
    return render_template('requests.html', requests=requests)


@app.route('/_response_email', methods=['GET', 'POST'])
def response_email():
    if request.method == 'POST':
        info = request.json
        recip = info[1]
        msg = info[0]
        template = render_template('email/response.html',msg=msg)
        send_response_email(email=recip,template=template)
    return "An email has been sent"


# This route is specifically to test the email functionality
# and will need to be re-purposed once scheduling is to be implemented
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