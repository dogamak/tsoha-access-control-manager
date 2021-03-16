#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tsoha import db
from tsoha.models import User

import bcrypt

def authenticate(username, password):
    user = User.query.filter(User.username == username).first()

    if user is None:
        return None

    if not bcrypt.checkpw(password.encode('utf-8'), user.password):
        return None

    return user

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def get_user(user_id):
    return User.query.filter(User.id == user_id).first()
