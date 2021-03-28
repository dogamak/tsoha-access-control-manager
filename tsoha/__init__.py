#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, Response, render_template, request, redirect, url_for, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, set_access_cookies, unset_access_cookies, current_user, get_jwt_identity, get_current_user, verify_jwt_in_request

import json

from sqlalchemy import and_, select
from sqlalchemy.orm import aliased, joinedload
import base64

from tsoha.config import get_config

app = Flask(__name__, template_folder='../build/templates', static_folder='../build')

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

from tsoha.models import User, Group, GroupMembership, File

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
        breadcrumb=[Link('Dashboard', 'default_route')],
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
    print(db.session.execute(select([User.username])))

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

class Link:
    def __init__(self, label, endpoint=None, **kwargs):
        self.label = label

        if endpoint:
            try:
                self.url = url_for(endpoint, **kwargs)
            except Exception:
                self.url = endpoint
        else:
            self.url = None
    
    def toJSON(self, shallow=False):
        return dict(label=self.label, url=self.url)

@app.route('/file/<id>', defaults={'name': None})
@app.route('/file/<id>/<name>')
def download_file(id, name):
    query = File.id == id

    if name is not None:
        query = query and File.name == name

    file = File.query.filter(query).first()

    if not file:
        return 'File Not Found', 404
    
    response = make_response(file.data)
    response.headers.set('Content-Type', file.mimetype)
    response.headers.set('Content-Disposition', 'attachment', filename=file.name or f'file_{file.id}')

    return response

@app.route('/groups')
@jwt_required()
def groups():
    groups = db.session.query(Group) \
        .join(GroupMembership) \
        .filter(GroupMembership.user_id == current_user.id) \
        .all()

    return render_component(
        'GroupListPage',
        breadcrumb=[Link('Groups', 'groups')],
        groups=groups,
    )

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
        breadcrumb=[Link('Groups', 'groups'), Link(group.name, 'group_details', id=id)],
        groups=groups,
        group=group,
        membership=membership,
    )

@app.route('/user/<username>')
@jwt_required()
def user_details(username):
    # .options(joinedload('groups.group.subgroups')) \

    user = User.query \
        .filter(User.username == username).first()

    if not user:
        return render_component(
            'NotFoundPage',
            message='No such user found.',
        )

    return render_component(
        'UserDetails',
        breadcrumb=[Link('Users'), Link(user.username, 'user_details', username=user.username)],
        user = user,
        groups = user.groups,
    )

@app.route('/user/<username>', methods=['POST'])
@jwt_required()
def user_edit(username):
    user = User.query.filter(User.username == username).first()

    if not user:
        return render_component(
            'NotFoundPage',
            message='No such user found.',
        )
    

    for field in ('name', 'username', 'email'):
        if field in request.form:
            setattr(user, field, request.form[field])
    
    db.session.commit()

    return redirect(url_for('user_details', username=user.username))

@app.route('/group/<group>/create_user')
@jwt_required()
def create_user_form(group):
    group = Group.query.filter(Group.id == group).first()

    return render_component('CreateUserPage', group=group)

def has_group_permission(group, user, permission):
    print(group, isinstance(group, Group))
    if not isinstance(group, Group):
        group = Group.query.filter(Group.id == group).first()

    if isinstance(user, int):
        user = User.query.filter(User.id == user).first()
    elif isinstance(user, str):
        user = User.query.filter(User.username == user).first()

    while group:
        membership = GroupMembership.query \
            .filter(GroupMembership.group == group and GroupMembership.user == user) \
            .first()

        if not membership:
            return False
        
        if getattr(membership, permission) is True:
            return True
        
        group = group.parent
    
    return False

@app.route('/user', methods=['POST'])
@jwt_required()
def create_user():
    json = request.get_json()
    user = get_current_user()

    new_user = User()

    for group in json.get('groups', []):
        group_def = Group.query.filter(Group.id == group['id']).first()

        if not has_group_permission(group_def, user, 'create_users'):
            return jsonify({
                'status': 'error',
                'field': 'groups',
                'error': f"User '{user.username}' (ID {user.id}) has no 'create_user' permission in group '{group_def.name}' (ID {group_def.id})",
            })
        
        new_user.groups.append(GroupMembership(
            user=new_user,
            group=group_def,
            create_users=group.get('create_users', False),
            manage_users=group.get('manage_users', False),
        ))
    
    if 'username' not in json or not json['username']:
        return jsonify({
            'status': 'error',
            'error': 'Username is required',
            'field': 'username',
        })

    if 'supervisor' in json:
        supervisor = User.query.filter(User.id == json['supervisor']).first()

        if not supervisor:
            return jsonify({
                'status': 'error',
                'error': f"Invalid supervisor: user with ID {json['supervisor']} does not exist",
                'field': 'supervisor',
            })
        
        new_user.supervisor = supervisor
    
    if 'photo' in json:
        try:
            avatar = File(uploader=user, owner=new_user)

            avatar.data = base64.b64decode(json['photo']['data'])
            avatar.mimetype = json['photo']['mimetype']

            new_user.avatar = avatar

        except Exception:
            return jsonify({
                'status': 'error',
                'error': 'Malformed data provided for the avatar image',
                'field': 'photo',
            })

    
    new_user.username = json.get('username')
    new_user.name = json.get('name')
    new_user.email = json.get('email')
    new_user.role = json.get('role')
    new_user.password = b""

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'user': new_user.toJSON(),
    })

def get_user_known_groups(user):
    groups = list(map(lambda m: m.group, user.groups))
    active = list(groups)
    new_active = []

    while len(active) > 0:
        for group in active:
            for subgroup in group.subgroups:
                if subgroup not in groups:
                    groups.append(subgroup)
                    new_active.append(subgroup)
            
            active = new_active
            new_active = []
    
    return groups

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

class DepthWrapper:
    def __init__(self, depth, value):
        self.depth = depth
        self.value = value

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        depth = 0

        if isinstance(obj, DepthWrapper):
            depth = obj.depth
            obj = obj.value

        if hasattr(obj, 'toJSON') and callable(obj.toJSON):
            d = {}

            delta = obj.__depth__ if hasattr(obj, '__depth__') else 1

            for key, value in obj.toJSON(shallow=depth > 1).items():
                if isinstance(value, (tuple, list, set)):
                    d[key] = [ DepthWrapper(depth + delta, v) for v in value ]
                else:
                    d[key] = DepthWrapper(depth + delta, value)
            
            return d

        return obj

app.json_encoder = CustomEncoder

def render_component(component, breadcrumb=[], **props):
    user = None

    try:
        verify_jwt_in_request(optional=True)
    except Exception as _e:
        pass
    else:
        if get_jwt_identity():
            user = get_current_user()
    
    users = []

    if user:
        u = aliased(User)
        gm1 = aliased(GroupMembership)
        gm2 = aliased(GroupMembership)

        stmt = db.session.query(gm1, gm2, User) \
            .filter(gm1.user_id == user.id) \
            .join(gm2, gm2.group_id == gm1.group_id) \
            .join(User, gm2.user_id == User.id) \
            .filter(User.id != user.id)

        print(stmt)

        users = User.query.select_from(gm1, gm2) \
            .filter(gm1.user_id == user.id) \
            .join(gm2, gm2.group_id == gm1.group_id) \
            .join(User, gm2.user_id == User.id) \
            .all()

        print(list(users))

    bootstrap = {
        'breadcrumb': breadcrumb,
        'router': router(),
        'user': user,
        'props': props,
        'groups': get_user_known_groups(user) if user else [],
        'users': users,
    }

    return render_template(component + '.html', bootstrap=json.dumps(bootstrap, cls=CustomEncoder))