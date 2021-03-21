#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, Response, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, set_access_cookies, unset_access_cookies, current_user, get_jwt_identity, get_current_user, verify_jwt_in_request

import json

from sqlalchemy import and_
from sqlalchemy.orm import aliased

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
    response = Response(render_component('LoginPage', error="Session expired. Please authenticate again.", username=user.username))
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

from tsoha.models import User, Group, GroupMembership

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
        user = get_current_user()

        return dict(
            authenticated=True,
            current_user=json.dumps({
                "id": user.id,
                "username": user.username,
            }),
        )

@app.route('/')
@jwt_required()
def default_route():
    groups = db.session.query(Group) \
        .join(GroupMembership) \
        .filter(GroupMembership.user_id == current_user.id) \
        .all()

    ms1 = aliased(GroupMembership)
    ms2 = aliased(GroupMembership)

    users = db.session.query(User) \
        .join(
            (ms1, ms1.user_id == User.id),
            (ms2, ms1.group_id == ms2.group_id),
        ) \
        .filter(GroupMembership.user_id == current_user.id) \
        .all()

    return render_component(
        'DashboardPage',
        groups=groups,
        users=users,
    )

@app.route('/login')
@jwt_required(optional=True)
def login_view():
    if get_jwt_identity():
        return redirect('/')

    return render_component('LoginPage')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    user = authenticate(username, password)

    if user is None:
        return render_component('LoginPage', error='Invalid credentials.', username=username)
    
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
    return render_component('EditorPage')

@app.route('/groups')
@jwt_required()
def groups():
    groups = db.session.query(Group) \
        .join(GroupMembership) \
        .filter(GroupMembership.user_id == current_user.id) \
        .all()

    return render_component('GroupListPage', groups=groups)

@app.route('/groups/<id>')
@jwt_required()
def group_details(id):
    membership = GroupMembership.query.filter(
        and_(
            GroupMembership.user_id == current_user.id,
            GroupMembership.group_id == id,
        )
    ).first()

    group = Group.query.filter(Group.id == id).first()

    groups = db.session.query(Group) \
        .join(GroupMembership) \
        .filter(GroupMembership.user_id == current_user.id) \
        .all()

    return render_component(
        'GroupDetailsPage',
        groups=groups,
        group=group,
        membership=membership,
    )

def router():
    router_map = '{'

    for rule in app.url_map.iter_rules():
        builder = '('

        if len(rule.arguments) > 0:
            builder += '{' + (', '.join(rule.arguments)) + '}'
        
        rule_expr = rule.rule

        for argument in rule.arguments:
            rule_expr = rule_expr.replace('<' + argument + '>', '${' + argument + '}')
        
        builder += ') => `' + rule_expr + '`'

        router_map += '"' + rule.endpoint + '": ' + builder + ', '
    
    router_map += '}'

    return router_map

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'toJSON') and callable(obj.toJSON):
            return obj.toJSON()
        
        return json.JSONEncoder.default(self, obj)

def render_component(component, **props):
    props = json.dumps(props, cls=CustomEncoder)
    return render_template('main.html', component=component, props=props, router=router())