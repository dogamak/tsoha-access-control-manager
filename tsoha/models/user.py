#!/usr/bin/env python
# -*- coding: utf-8 -*-

import enum

from sqlalchemy.orm.collections import mapped_collection
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

from flask import url_for

from tsoha import db
from tsoha.models import Base

class User(Base):
    __public__ = ('id', 'name', 'username', 'email', 'role', 'supervisor', 'avatar')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    role = db.Column(db.String)
    supervisor_id = db.Column(db.Integer, db.ForeignKey(id))
    password = db.Column(db.LargeBinary, nullable=False)
    avatar_id = db.Column(db.Integer, db.ForeignKey('file.id'))

    avatar = db.relationship('File', foreign_keys=[avatar_id], post_update=True)
    supervisor = db.relationship('User', remote_side=[id], backref='subordinates')

class File(Base):
    id = db.Column(db.Integer, primary_key=True)

    uploader_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String, nullable=False)
    name = db.Column(db.String)

    uploader = db.relationship('User', foreign_keys=[uploader_id])
    owner = db.relationship('User', backref='files', foreign_keys=[owner_id])

    def toJSON(self, shallow=False):
        return { 'url': url_for('download_file', id=self.id, name=self.name) }