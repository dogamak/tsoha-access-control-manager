#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tsoha import db
from tsoha.models import User

from sqlalchemy import Table, and_

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey(id))
    parent = db.relationship("Group", remote_side=[id], backref="subgroups")

    def toJSON_shallow(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def toJSON(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent": self.parent.toJSON_shallow() if self.parent else None,
            "subgroups": [ sub.toJSON_shallow() for sub in self.subgroups ],
            "members": [ membership.user for membership in self.members ],
        }

class GroupMembership(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    create_users = db.Column(db.Boolean, default=False, nullable=False)
    manage_users = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship(User, backref='groups')
    group = db.relationship(Group, backref='members')

    def toJSON(self):
        return {
            "user": self.user,
            "group": self.group,
            "create_users": self.create_users,
            "manage_users": self.manage_users,
        }
