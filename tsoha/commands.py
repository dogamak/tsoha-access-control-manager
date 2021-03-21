#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bcrypt
import click

from flask.cli import with_appcontext

from tsoha import db, app
from tsoha.auth import hash_password
from tsoha.models import User, Group, GroupMembership

@click.command(name='create-user')
@click.argument('username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_user(username, password):
    hashed = hash_password(password)

    user = User(username=username, password=hashed)

    db.session.add(user)
    db.session.commit()

    print(f'Created user with username {username} and ID {user.id}.')

@click.command(name='create-group')
@click.argument('name')
@click.option('--parent')
def create_group(name, parent=None):
    group = Group(name=name)

    if parent is not None:
        p = Group.query.filter(Group.name == parent).first()
        group.parent = p

    db.session.add(group)
    db.session.commit()

    print(f'Created group \'{name}\' with ID {group.id}.')

@click.command(name='add-to-group')
@click.argument('group')
@click.argument('username')
@click.option('--create-users', is_flag=True)
@click.option('--manage-users', is_flag=True)
@with_appcontext
def add_to_group(group, username, create_users=False, manage_users=False):
    g = Group.query.filter(Group.name==group).first()
    u = User.query.filter(User.username==username).first()
    m = GroupMembership(group_id=g.id, user_id=u.id, create_users=create_users, manage_users=manage_users)

    db.session.add(m)
    db.session.commit()

    print(f'Added user \'{ username }\' to group \'{ group }\'.')

app.cli.add_command(create_user)
app.cli.add_command(create_group)
app.cli.add_command(add_to_group)
