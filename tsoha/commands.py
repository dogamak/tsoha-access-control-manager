#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bcrypt
import click

from flask.cli import with_appcontext

from tsoha import db, app
from tsoha.auth import hash_password
from tsoha.models import User

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

app.cli.add_command(create_user)
