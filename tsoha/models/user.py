#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tsoha import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)

