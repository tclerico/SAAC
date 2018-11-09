from flask import flash, redirect, request, jsonify, current_app
from app.models import *
from flask_login import current_user, login_user, logout_user, login_required
from flask import render_template, flash, redirect, url_for, request, jsonify
from app.forms import LoginForm, NewRequestForm, RegistrationForm
from app.token import *
from app.email import *
from collections import defaultdict

def subjects_from_file():
    with open('subjects.txt') as f:
        subjects = f.readlines()
    # strip all new line characters
    subjects = [x.strip() for x in subjects]

    subs = list()
    # info ={"courses":[]}
    for s in subjects:
        subs.append(s.split(","))

    return subs

def process_expertise_change(inputs):
    sent = []
    for i in inputs:
        sent.append(Expertise.query.filter_by(course_prefix=i.split('-')[0],
                                              course_level=i.split('-')[1]).first())

    user = User.query.get(current_user.id)
    current = user.fields.all()

    # TODO MAKE THE APPEND/REMOVE MORE EFFICIENT --> use Counter?
    # checks the sent fields against current fields
    # looks for expertise that exist in sent but not in current fields
    # adds the new fields
    for s in sent:
        if s not in current:
            user.fields.append(s)


    # looks for expertise that exist in current but not in sent
    # removes them from current
    for c in current:
        if c not in sent:
            user.fields.remove(c)

    db.session.commit()


def create_new_request(form):
    #get prefix + number and find the corresponding expertise
    prefix = form.c_prefix.data
    prefix = prefix.upper()
    number = int(form.c_number.data)
    level = (int(number / 100)) * 100
    exp = Expertise.query.filter_by(
        course_prefix=prefix, course_level=level).first()

    # normal form activity
    title = form.title.data
    descrip = form.description.data

    retRequest = Request(uid=current_user.id, expertise_id=exp.id,
                         title=title, description=descrip, is_active=True, expertise=exp)
    db.session.add(retRequest)
    db.session.commit()

    return (retRequest.id)


def validRequest(form):
    valid = True

    expertise = Expertise.query.all()
    pref = form.c_prefix.data
    pref = pref.upper()
    number = int(form.c_number.data)
    level = (int(number / 100)) * 100

    exPref = []
    for e in expertise:
       exPref.append(e.course_prefix)

    if exPref.count(pref) < 1:
        valid = False

    if level > 400:
        valid = False

    return valid


def sort_requests(reqs):
    ur = defaultdict(int)
    for r in reqs:
        ur[str(r.expertise)] = current_app.expert_population[str(r.expertise)]

    sorted_exp = sorted(ur.items(), key=lambda k_v: k_v[1])
    reqsCopy = reqs
    sorted_reqs = []

    for i in range(0, len(sorted_exp)):
        for j in range(0, len(reqsCopy)):
            if str(reqsCopy[j].expertise) == sorted_exp[i][0]:
                sorted_reqs.append(reqsCopy[j])

    return sorted_reqs


def register_user(form):
    tparse = form.email.data
    parsed = tparse.split("@")[0]

    # create user
    user = User(name=parsed, email=form.email.data, class_year=form.class_year.data,
                department=form.department.data, sport=form.sport.data, sec_sport=form.sec_sport.data, confirmed=False)
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
    return user


def count_population():
    exp = Expertise.query.all()
    population = defaultdict(int)
    # creates a list of dictionaries e.g. [{'expertise':'COMP 200', 'population': 3}, {'expertise':'MATH 100', 'population': 1}]
    for e in exp:
        pop = len(User.query.join(User.fields).filter_by(id=e.id).all())
        if pop > 0:
            population[str(e)] = pop
    return population
