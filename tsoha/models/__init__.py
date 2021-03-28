#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tsoha import db

from sqlalchemy.orm.relationships import RelationshipProperty

class Base(db.Model):
    __abstract__ = True
    __public__ = []

    def toJSON(self, shallow=False):
        json = {}

        for key in self.__public__:
            value = getattr(self, key)

            if shallow and isinstance(getattr(self.__class__, key).property, RelationshipProperty):
                continue

            json[key] = value

        return json

from .user import User, File
from .group import Group, GroupMembership
