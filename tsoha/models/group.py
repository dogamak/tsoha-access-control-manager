#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tsoha import db
from tsoha.models import User, Base

from sqlalchemy import Table, and_

class Group(Base):
    __public__ = ('id', 'name', 'parent', 'subgroups', 'members')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey(id))
    parent = db.relationship("Group", remote_side=[id], backref="subgroups")

class GroupMembership(Base):
    __depth__ = 0
    __public__ = ('user', 'group', 'create_users', 'manage_users')

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    create_users = db.Column(db.Boolean, default=False, nullable=False)
    manage_users = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship(User, backref='groups')
    group = db.relationship(Group, backref='members')
