#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, Response, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, set_access_cookies, unset_access_cookies, current_user, get_jwt_identity, get_current_user, verify_jwt_in_request

from tsoha.config import get_config

app = Flask(__name__, template_folder='../templates', static_folder='../dist')

get_config(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from tsoha.auth import authenticate, get_user

jwt = JWTManager(app)

@jwt.user_identity_loader
def jwt_identity_loader(user):
    return user.id

@jwt.user_lookup_loader
def jwt_user_loader(_jwt_header, jwt_data):
    return get_user(jwt_data["sub"])

@jwt.expired_token_loader
def expired_token_loader(_jwt_header, jwt_data):
    user = get_user(jwt_data["sub"])
    response = Response(render_template("login.html", message="Session expired. Please authenticate again.", username=user.username))
    unset_access_cookies(response)
    return response

@jwt.unauthorized_loader
def invalid_token_loader(reason):
    response = redirect(url_for('login_view'))
    unset_access_cookies(response)
    return response


import tsoha.commands
import tsoha.models

db.create_all()

from tsoha.models import User

@app.context_processor
def current_user_context():
    try:
        verify_jwt_in_request(optional=True)
    except Exception as e:
        return dict(
            authenticated=False,
            current_user=None,
        )

    if not get_jwt_identity():
        return dict(
            authenticated=False,
            current_user=None,
        )
    else:
        return dict(
            authenticated=True,
            current_user=get_current_user(),
        )

@app.route('/')
@jwt_required()
def default_route():
    return render_template('dashboard.html')

@app.route('/login')
@jwt_required(optional=True)
def login_view():
    if get_jwt_identity():
        return redirect('/')

    return render_template('login.html')

@app.route('/secret')
@jwt_required()
def secret():
    return 'secret: ' + current_user.username

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    user = authenticate(username, password)

    if user is None:
        return render_template('login.html', message='Invalid credentials.', username=username)
    
    token = create_access_token(identity=user)
    response = redirect('/')
    set_access_cookies(response, token)
    return response

@app.route('/logout')
def logout():
    response = redirect(url_for('login_view'))
    unset_access_cookies(response)
    return response

@app.route('/editor')
def editor():
    return render_template('editor.html')
