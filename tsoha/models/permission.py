from tsoha import db
from tsoha.models import Base, User, Group, GroupMembership
from tsoha.permissions.model import ObjectModel, ObjectDefinition, Permission as ModelPermission
from tsoha.permissions.fluent import PermissionConstructor

from sqlalchemy import select, join, exists, not_, and_
from sqlalchemy.orm import aliased

class Permission(db.Model):
    name = db.Column(db.String, primary_key=True)

class PermissionInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    permission_id = db.Column(db.String, db.ForeignKey(Permission.name), nullable=False)
    expr = db.Column(db.String, nullable=False)
    super_permission_id = db.Column(db.Integer, db.ForeignKey(id))
    super_permission_parameter_number = db.Column(db.Integer)

    permission = db.relationship(Permission)
    super_permission = db.relationship('PermissionInstance', remote_side=[id])

class PermissionArgument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    permission_instance_id = db.Column(db.Integer, db.ForeignKey(PermissionInstance.id), nullable=False)
    argument_number = db.Column(db.Integer, nullable=False)
    object_type = db.Column(db.String, nullable=False)
    object_id = db.Column(db.Integer, nullable=False)

    permission_instance = db.relationship(PermissionInstance)


secondary_join = lambda s:   lambda a, q: select([a]).select_from(join(q, s).join(a))
join_on_remote = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(a, key) == q.id))
join_on_local  = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(q, key) == a.id))


class PermissionObjectModel(ObjectModel):
    user = ObjectDefinition(User) \
        .relation('groups', 'group', joiner=secondary_join(GroupMembership)) \
        .relation('subordinates', 'user', joiner=join_on_remote('supervisor_id')) \
        .relation('supervisor', 'user', joiner=join_on_local('supervisor_id')) \
        .add_filter('id', primary_key=True) \
        .add_filter('username', unique=True)
    
    group = ObjectDefinition(Group) \
        .relation('members', 'user', joiner=secondary_join(GroupMembership)) \
        .relation('subgroups', 'group', joiner=join_on_remote('parent_id')) \
        .relation('parent', 'group', joiner=join_on_local('parent_id'), is_singular=True) \
        .add_filter('id', primary_key=True)

    create_user = ModelPermission(['current_user', 'target_group'])
    add_to_group = ModelPermission(['current_user', 'target_user', 'target_group'])
    remove_from_group = ModelPermission(['current_user', 'target_user', 'target_group'])