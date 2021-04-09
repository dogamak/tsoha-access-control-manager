from tsoha import db
from tsoha.models import Base, User, Group, GroupMembership
from tsoha.permissions.model import ObjectModel, ObjectDefinition, Permission as ModelPermission
from tsoha.permissions.fluent import PermissionConstructor

from sqlalchemy import select, join, exists, not_, and_
from sqlalchemy.orm import aliased
from sqlalchemy.ext.ordering_list import ordering_list

class PermissionExpression(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    permission_name = db.Column(db.String)
    parent_expression_id = db.Column(db.Integer, db.ForeignKey(id))
    parent_expression_argument_index = db.Column(db.Integer)
    expression = db.Column(db.String, nullable=False)

    parent_expression = db.relationship(
        'PermissionExpression',
        remote_side=[id],
        backref='arguments',
    )

    arguments = db.relationship(
        'PermissionExpression',
        order_by=parent_expression_argument_index,
        collection_class=ordering_list(
            parent_expression_argument_index,
            count_from=0,
        ),
    )


class ExpressionMatch(db.Model):
    expression_id = db.Column(db.Integer, db.ForeignKey(PermissionExpression.id), primary_key=True)
    object_type = db.Column(db.String, primary_key=True)
    object_id = db.Column(db.Integer, primary_key=True)

    expression = db.relationship(
        'PermissionExpression',
        backpopulated='matches',
    )


secondary_join = lambda s:   lambda a, q: select([a]).select_from(join(q, s).join(a))
join_on_remote = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(a, key) == q.id))
join_on_local  = lambda key: lambda a, q: select([a]).select_from(join(q, a, getattr(q, key) == a.id))


class PermissionObjectModel(ObjectModel):
    user = ObjectDefinition(User) \
        .relation('groups',       Group, secondary=GroupMembership) \
        .relation('subordinates', User,  remote_field='supervisor_id') \
        .relation('supervisor',   User,  local_field='supervisor_id') \
        .add_filter('id', primary_key=True) \
        .add_filter('username', unique=True)
    
    group = ObjectDefinition(Group) \
        .relation('members',   User,  secondary=GroupMembership) \
        .relation('subgroups', Group, remote_field='parent_id') \
        .relation('parent',    Group, local_field='parent_id') \
        .add_filter('id', primary_key=True)

    create_user = ModelPermission(['current_user', 'target_group'])
    add_to_group = ModelPermission(['current_user', 'target_user', 'target_group'])
    remove_from_group = ModelPermission(['current_user', 'target_user', 'target_group'])